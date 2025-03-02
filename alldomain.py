import argparse
import socket
import time
from threading import Thread
from urllib.parse import urlparse
import requests
from art import tprint
from colorama import Fore


def define_args():
    """
        Esta função define os argumentos do programa e retorna o objeto ArgumentParser (parser)
    """
    parser = argparse.ArgumentParser(
        prog="AllDomain",
        description="Look for subdomains on a HTTP web server within a same IP address. Good for cybersecurity labs :-)",
        epilog="Usage: python alldomain.py -w [WORDLIST] -p [PORT] -d [DELAY] [HOST IP]"
    )
    parser.add_argument('-w', '--wordlist', action='store')
    parser.add_argument('-p', '--port', action='store', default=80, type=int)
    parser.add_argument('HOST', action='store', help="The IP of the HTTP web server.")
    parser.add_argument('-d', '--delay', action='store', default=0,
                        help="The delay in seconds after creating the defined number of threads (default is 10).",
                        type=float)
    parser.add_argument('-t', '--threads', action='store', default=10,
                        help="Number of simultaneous HTTP requests made by a thread.", type=int)
    return parser


def get_args(parser: argparse.ArgumentParser):
    """
        Esta função verifica se todos os argumentos foram recebidos e os retorna
        em forma de dicionário (dict)
    """
    args = parser.parse_args()
    if not args.wordlist:
        parser.print_help()
        exit(0)
    return dict(wordlist=args.wordlist, port=args.port, delay=args.delay, host=args.HOST, threads=args.threads)


def print_found_message(subdomain: str, status_code: int):
    """
        Função para mostrar uma mensagem quando algum subdomínio for encontrado.
    """
    print(f"{Fore.GREEN}[{status_code}]{Fore.RESET} {subdomain}.{DOMAIN}")


def get_domain(host: str, port: int):
    """
        Essa função retorna o domínio do servidor a partir do cabeçalho 'Location' da resposta HTTP e o formata
        usando as funções join e split.
    """
    headers = {"user-agent": "Mozilla/5.0 (Linux; U; Linux x86_64) Gecko/20100101 Firefox/74.8"}
    request = requests.get(f"http://{host}:{port}/", headers=headers, allow_redirects=False)
    location = request.headers.get("location")

    if location:
        domain = ('.'.join(urlparse(location).netloc.split('.')[-2:]))
    else:
        domain = socket.gethostbyaddr(host)[0]
    assert domain is not None, f"Couldn't find the domain for IP '{host}'"
    return domain


def request_subdomain(subdomain: str, host: str, port: int):
    """
        Essa função é chamada por cada Thread usando uma string de subdomínio diferente.
        Os Threads fazem uma requisição para a página '/' e verificam se o subdomínio existe
        baseado na resposta HTTP.
    """
    headers = {
        "user-agent": "Mozilla/5.0 (Linux; U; Linux x86_64) Gecko/20100101 Firefox/74.8",
        "host": f"{subdomain}.{DOMAIN}"
    }
    url = f"http://{host}:{port}/"
    pass
    request = requests.get(url, headers=headers, allow_redirects=False)
    if request.status_code != 404:
        print_found_message(subdomain, request.status_code)
        pass


def print_logo():
    print(Fore.YELLOW)
    tprint("AllDomain")
    print(Fore.RESET)


def print_config(configs: dict):
    """
        Função para mostrar os argumentos passados ao programa.
    """
    print(f"Host IP: {configs.get("host")}")
    print(f"Port: {configs.get("port")}")
    print(f"Wordlist: {configs.get("wordlist")}")
    print(f"Threads: {configs.get("threads")}")
    print(f"Delay: {configs.get("delay")}\n")


if __name__ == "__main__":
    # Exibe a logo e créditos ao programador
    print_logo()
    print(f"{Fore.MAGENTA}{'-' * 16} Developed by Mardson Diego {'-' * 16}{Fore.RESET}")

    try:
        # Recebe os argumentos (IP, porta, dicionário de palavras)
        args = get_args(define_args())
        print_config(args)

        # Salva os argumentos em variáveis
        PORT = args.get("port")
        IP = args.get("host")
        DOMAIN = get_domain(IP, PORT)
        DELAY = args.get("delay")
        THREADS = args.get('threads')

        # Abre o dicionário de palavras
        with open(args.get('wordlist'), 'r') as wordlist:
            working_threads = list()
            print(f"{Fore.BLUE}[INFO] Searching domains by requests...{Fore.RESET}")

            # Itera sobre as palavras e cria um Thread para requisitar o servidor com uma palavra
            for word in wordlist:
                if len(working_threads) < THREADS:
                    thread = Thread(target=request_subdomain, args=[word.strip(), IP, PORT])
                    thread.start()
                    working_threads.append(thread)
                else:
                    # Quando cria o número de Threads definida pelo usuário, pausa por alguns segundos
                    for thread in working_threads:
                        thread.join()
                    # Limpa todos os Threads e continua as requisições
                    time.sleep(DELAY)
                    working_threads.clear()
    except Exception as e:
        print(f"[ERROR] {e}")
