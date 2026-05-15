import colorama

def tokenize(string):
    '''
    "/command set value" -> ["/command", "set", "value"]
    '''
    return string.split(" ")

def detokenize(tokens):
    '''
    ["/command", "set", "value"] -> "/command set value"
    '''
    return " ".join(tokens)

def log(message, level="INFO"):
    if level == "INFO":
        print(f"{colorama.Fore.GREEN}[INFO]{colorama.Style.RESET_ALL} {message}")
    elif level == "WARNING":
        print(f"{colorama.Fore.YELLOW}[WARN]{colorama.Style.RESET_ALL} {message}")
    elif level == "ERROR":
        print(f"{colorama.Fore.RED}[ERROR]{colorama.Style.RESET_ALL} {message}")
    elif level == "DEBUG":
        print(f"{colorama.Fore.BLUE}[DEBUG]{colorama.Style.RESET_ALL} {message}")
    else:
        print(f"{colorama.Fore.WHITE}[{level}]{colorama.Style.RESET_ALL} {message}")
