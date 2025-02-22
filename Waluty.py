import requests
import pandas as pd
from datetime import datetime
import time
import sys
from github import Github, GithubException
import os
import base64

class CurrencyMonitor:
    def __init__(self, github_token, repo_name, filename='kursy_walut.csv'):
        """
        Inicjalizacja monitora kursów walut
        """
        self.filename = filename
        self.github = Github(github_token)
        self.repo_name = repo_name

    def get_exchange_rates(self):
        """
        Pobiera kursy walut USD/PLN i CHF/PLN z API NBP
        """
        try:
            # Pobieranie kursu USD/PLN
            usd_response = requests.get('http://api.nbp.pl/api/exchangerates/rates/a/usd/')
            usd_data = usd_response.json()
            usd_rate = usd_data['rates'][0]['mid']

            # Pobieranie kursu CHF/PLN
            chf_response = requests.get('http://api.nbp.pl/api/exchangerates/rates/a/chf/')
            chf_data = chf_response.json()
            chf_rate = chf_data['rates'][0]['mid']

            return usd_rate, chf_rate

        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas pobierania danych: {e}")
            return None, None
        except (KeyError, IndexError) as e:
            print(f"Błąd w strukturze odpowiedzi API: {e}")
            return None, None

    def push_to_github(self, df):
        """
        Wysyła dane do GitHub
        """
        try:
            # Pobieranie repozytorium
            repo = self.github.get_repo(self.repo_name)
            
            # Przygotowanie zawartości pliku
            csv_content = df.to_csv(index=False)
            
            try:
                # Próba pobrania istniejącego pliku
                file = repo.get_contents(self.filename)
                # Aktualizacja pliku
                repo.update_file(
                    path=self.filename,
                    message=f"Aktualizacja kursów walut {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    content=csv_content,
                    sha=file.sha,
                    branch="main"
                )
                print(f"Zaktualizowano plik na GitHub: {self.filename}")
            
            except GithubException as e:
                if e.status == 404:
                    # Tworzenie nowego pliku
                    repo.create_file(
                        path=self.filename,
                        message=f"Utworzenie pliku z kursami walut {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        content=csv_content,
                        branch="main"
                    )
                    print(f"Utworzono nowy plik na GitHub: {self.filename}")
                else:
                    raise e
                    
        except Exception as e:
            print(f"Błąd podczas operacji na GitHub: {e}")
            print(f"Szczegóły błędu: {str(e)}")

    def save_locally(self, df):
        """
        Zapisuje dane lokalnie
        """
        try:
            df.to_csv(self.filename, index=False)
            print(f"Zapisano dane lokalnie do {self.filename}")
        except Exception as e:
            print(f"Błąd podczas zapisywania lokalnego: {e}")

    def update_data(self, usd_rate, chf_rate):
        """
        Aktualizuje dane lokalnie i na GitHub
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # Wczytanie istniejącego pliku lub utworzenie nowego DataFrame
            try:
                df = pd.read_csv(self.filename)
            except FileNotFoundError:
                df = pd.DataFrame(columns=['timestamp', 'USD/PLN', 'CHF/PLN'])

            # Przygotowanie nowego wiersza
            new_row = pd.DataFrame({
                'timestamp': [current_time],
                'USD/PLN': [float(usd_rate)],
                'CHF/PLN': [float(chf_rate)]
            })

            # Połączenie danych
            if df.empty:
                df = new_row
            else:
                df = pd.concat([df, new_row], ignore_index=True)

            # Zapisanie danych
            self.save_locally(df)
            self.push_to_github(df)

        except Exception as e:
            print(f"Błąd podczas aktualizacji danych: {e}")

    def run(self, interval=300):
        """
        Uruchamia monitoring kursów walut
        """
        print("Start monitorowania kursów walut...")
        print(f"Dane będą zapisywane do pliku: {self.filename}")
        print("Wciśnij Ctrl+C aby zakończyć")
        
        try:
            while True:
                usd_rate, chf_rate = self.get_exchange_rates()
                
                if usd_rate is not None and chf_rate is not None:
                    self.update_data(usd_rate, chf_rate)
                else:
                    print("Nie udało się pobrać kursów walut")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nZakończono monitorowanie kursów walut")
            sys.exit(0)

def main():
    # Konfiguracja
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    REPO_NAME = os.getenv('GITHUB_REPO')
    
    if not GITHUB_TOKEN or not REPO_NAME:
        print("Błąd: Ustaw zmienne środowiskowe GITHUB_TOKEN i GITHUB_REPO")
        sys.exit(1)
    
    # Utworzenie i uruchomienie monitora
    monitor = CurrencyMonitor(GITHUB_TOKEN, REPO_NAME)
    monitor.run()

if __name__ == "__main__":
    main()