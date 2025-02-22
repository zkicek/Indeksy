import yfinance as yf
from github import Github
import pandas as pd
from datetime import datetime
import time
import os
import requests

class IndeksMonitor:
    def __init__(self, github_token, repo_name):
        self.github = Github(github_token)
        self.repo = self.github.get_repo(repo_name)
        self.data_file = 'data.csv'
        self.ostatnia_wartosc_dax = None
        self.ostatnia_wartosc_sp500 = None
        self.czas_ostatniego_zapytania = None

    def sprawdz_dostepnosc_yf(self):
        """Sprawdza czy serwis Yahoo Finance jest dostępny"""
        try:
            # Próbujemy pobrać podstawowe dane testowe
            msft = yf.Ticker("MSFT")
            info = msft.info
            if info and 'regularMarketPrice' in info:
                return True
            return False
        except Exception as e:
            print(f"\nBłąd dostępu do Yahoo Finance: {e}")
            return False

    def sprawdz_godziny_handlu(self):
        """Sprawdza czy giełdy są otwarte"""
        now = datetime.now()
        
        # Sprawdź czy jest weekend
        #if now.weekday() >= 5:
        #    print("\nWeekend - giełdy zamknięte")
        #    return False
            
        # Sprawdź dostępność serwisu
        if not self.sprawdz_dostepnosc_yf():
            print("\nSerwis Yahoo Finance niedostępny - możliwa przerwa techniczna")
            return False
            
        return True

    def pobierz_indeks(self, symbol, nazwa):
        """Pobiera dane dla pojedynczego indeksu z obsługą błędów"""
        max_proby = 3
        for proba in range(max_proby):
            try:
                if self.czas_ostatniego_zapytania:
                    czas_od_ostatniego = (datetime.now() - self.czas_ostatniego_zapytania).total_seconds()
                    if czas_od_ostatniego < 30:
                        time.sleep(30 - czas_od_ostatniego)
                
                dane = yf.download(symbol, period="1d", interval="15m")
                self.czas_ostatniego_zapytania = datetime.now()
                
                if len(dane) > 0:
                    return float(dane['Close'].iloc[-1])
                return None
                
            except Exception as e:
                print(f"\nBłąd podczas pobierania {nazwa} (próba {proba + 1}/{max_proby}): {e}")
                if not self.sprawdz_dostepnosc_yf():
                    print("Serwis niedostępny - czekam 5 minut przed kolejną próbą...")
                    time.sleep(300)
                elif proba < max_proby - 1:
                    czas_oczekiwania = 60 * (proba + 1)
                    print(f"Czekam {czas_oczekiwania} sekund przed ponowną próbą...")
                    time.sleep(czas_oczekiwania)
        return None
    
    def pobierz_aktualne_wartosci(self):
        """Pobiera aktualne wartości indeksów"""
        if not self.sprawdz_godziny_handlu():
            return None
            
        dax = self.pobierz_indeks("^GDAXI", "DAX 40")
        if dax is not None:
            sp500 = self.pobierz_indeks("^GSPC", "S&P 500")
            
            if dax is not None and sp500 is not None:
                return {
                    'DAX 40': dax,
                    'S&P 500': sp500
                }
        return None

def main():
    github_token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPO')
    
    if not github_token or not repo_name:
        print("Ustaw zmienne środowiskowe GITHUB_TOKEN i GITHUB_REPO")
        return
    
    monitor = IndeksMonitor(github_token, repo_name)
    print("Rozpoczęto monitorowanie indeksów...")
    print("Naciśnij Ctrl+C aby zakończyć")
    
    try:
        while True:
            aktualne_wartosci = monitor.pobierz_aktualne_wartosci()
            if aktualne_wartosci and monitor.czy_wartosci_sie_zmienily(aktualne_wartosci):
                monitor.zapisz_do_github(aktualne_wartosci)
            else:
                print(".", end="", flush=True)
            time.sleep(900)  # Sprawdzaj co 15 minut
            
    except KeyboardInterrupt:
        print("\nZakończono monitorowanie indeksów")

if __name__ == "__main__":
    main()