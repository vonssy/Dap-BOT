from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from nacl.signing import SigningKey
from base58 import b58decode, b58encode
from base64 import b64encode
from dotenv import load_dotenv
from datetime import datetime
from colorama import *
import asyncio, random, json, re, os, pytz

load_dotenv()

wib = pytz.timezone('Asia/Jakarta')

class DAP:
    def __init__(self) -> None:
        self.BASE_API = "https://api.dapcoin.xyz/api"
        self.REF_CDOE = "X9Y5S0VQ" # U can change it with yours
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}
        self.min_score = int(os.getenv("MIN_SCORE").strip())
        self.max_score = int(os.getenv("MAX_SCORE").strip())

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}DAP {Fore.BLUE + Style.BRIGHT}Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")

    def generate_address(self, account: str):
        try:
            decode_account = b58decode(account)
            signing_key = SigningKey(decode_account[:32])
            verify_key = signing_key.verify_key
            address = b58encode(verify_key.encode()).decode()
            
            return address
        except Exception as e:
            return None
        
    def generate_payload(self, account: str, address: str, nonce: str):
        try:
            decode_account = b58decode(account)
            signing_key = SigningKey(decode_account[:32])
            message_bytes = nonce.encode('utf-8')
            signature = signing_key.sign(message_bytes).signature
            signature_base64 = b64encode(signature).decode()
            
            payload = {
                "signature": signature_base64,
                "wallet_address": address
            }
            
            return payload
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed {str(e)}")

    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = (
                        "With" if proxy_choice == 1 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

        rotate_proxy = False
        if proxy_choice == 1:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate_proxy in ["y", "n"]:
                    rotate_proxy = rotate_proxy == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return proxy_choice, rotate_proxy
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None
    
    async def auth_login(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/auth/login"
        data = json.dumps({"wallet_address": address, "ref": self.REF_CDOE, "email": None, "username": None})
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Login Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def auth_verify(self, account: str, address: str, nonce: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/auth/verify"
        data = json.dumps(self.generate_payload(account, address, nonce))
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Verify Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def user_info(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/me"
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch User Info Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def checkin_status(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/checkin/status"
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch Status Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def claim_checkin(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/checkin"
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": "0",
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Claim Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def start_game(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/games/dc591e39-8abf-42f3-880d-02de96cb71d9/start"
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": "0",
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        print(f"{response.status}:{await response.text()}")
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT}     > {Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT}Start  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def complete_game(self, address: str, game_id: str, score: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/games/dc591e39-8abf-42f3-880d-02de96cb71d9/complete"
        data = json.dumps({"id": game_id, "score": score})
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        print(f"{response.status}:{await response.text()}")
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT}     > {Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT}Finish :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def task_lists(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/tasks"
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Tasks   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch List Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def complete_task(self, address: str, task_id: str, title: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/tasks/{task_id}/complete"
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": "0"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT}   > {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Completed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None

    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if is_valid: return True

            if rotate_proxy:
                proxy = self.rotate_proxy_for_account(address)
                await asyncio.sleep(1)
                continue

            return False
            
    async def process_user_login(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            login = await self.auth_login(address, proxy)
            if not login: return False

            message = login.get("message", None)
            if message and message == "Wallet not verified, Sign the nonce to verify":
                nonce = login["nonce"]

                verify = await self.auth_verify(account, address, nonce, proxy)
                if not verify: return False

                self.access_tokens[address] = verify["token"]

            else:
                self.access_tokens[address] = login["token"]

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Login Success {Style.RESET_ALL}"
            )

            return True

    async def process_accounts(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        logined = await self.process_user_login(account, address, use_proxy, rotate_proxy)
        if logined:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            user =  await self.user_info(address, proxy)
            if not user: return

            points = user.get("points", 0)
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {points} DAP {Style.RESET_ALL}"
            )

            checkin = await self.checkin_status(address, proxy)
            if checkin:
                has_checkin = checkin.get("checked_in_today")

                if not has_checkin:
                    claim = await self.claim_checkin(address, proxy)
                    if claim:
                        reward = claim.get("points_awarded")

                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT} Claimed {Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                            f"{Fore.CYAN+Style.BRIGHT} Reward: {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{reward} DAP{Style.RESET_ALL}"
                        )

                else:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                    )

            # remaining_trials = user.get("tickets", 0)
            # if remaining_trials > 0:
            #     self.log(f"{Fore.CYAN+Style.BRIGHT}Games   :{Style.RESET_ALL}")

            #     for i in range(remaining_trials):
            #         self.log(
            #             f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
            #             f"{Fore.WHITE+Style.BRIGHT}{i+1} Of {remaining_trials}{Style.RESET_ALL}"
            #         )

            #         start = await self.start_game(address, proxy)
            #         if not start: continue

            #         game_id = start.get("game", {}).get("id")

            #         self.log(
            #             f"{Fore.MAGENTA+Style.BRIGHT}     > {Style.RESET_ALL}"
            #             f"{Fore.BLUE+Style.BRIGHT}Start  :{Style.RESET_ALL}"
            #             f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            #         )
            #         self.log(
            #             f"{Fore.MAGENTA+Style.BRIGHT}     > {Style.RESET_ALL}"
            #             f"{Fore.BLUE+Style.BRIGHT}Game Id:{Style.RESET_ALL}"
            #             f"{Fore.WHITE+Style.BRIGHT} {game_id} {Style.RESET_ALL}"
            #         )

            #         score = random.randint(self.min_score, self.max_score)

            #         complete = await self.complete_game(address, game_id, score, proxy)
            #         if not complete: continue

            #         self.log(
            #             f"{Fore.MAGENTA+Style.BRIGHT}     > {Style.RESET_ALL}"
            #             f"{Fore.BLUE+Style.BRIGHT}Finish :{Style.RESET_ALL}"
            #             f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            #         )
            #         self.log(
            #             f"{Fore.MAGENTA+Style.BRIGHT}     > {Style.RESET_ALL}"
            #             f"{Fore.BLUE+Style.BRIGHT}Score  :{Style.RESET_ALL}"
            #             f"{Fore.WHITE+Style.BRIGHT} {score}m {Style.RESET_ALL}"
            #         )

            # else:
            #     self.log(
            #         f"{Fore.CYAN+Style.BRIGHT}Games   :{Style.RESET_ALL}"
            #         f"{Fore.YELLOW+Style.BRIGHT} No Avaialble Trials {Style.RESET_ALL}"
            #     )

            
            tasks = await self.task_lists(address, proxy)
            if tasks:
                self.log(f"{Fore.CYAN+Style.BRIGHT}Tasks   :{Style.RESET_ALL}")

                task_lists = tasks.get("data", [])

                for task in task_lists:
                    task_id = task.get("id")
                    title = task.get("title")
                    reward = task.get("points")
                    is_completed = task.get("user_completion", None)

                    if is_completed:
                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT}   > {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                        )
                        continue

                    complete = await self.complete_task(address, task_id, title, proxy)
                    if complete:
                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT}   > {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT} Completed {Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                            f"{Fore.CYAN+Style.BRIGHT} Reward: {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{reward} DAP{Style.RESET_ALL}"
                        )
            
    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            proxy_choice, rotate_proxy = self.print_question()

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                use_proxy = True if proxy_choice == 1 else False
                if use_proxy:
                    await self.load_proxies()
                
                separator = "=" * 23
                for idx, account in enumerate(accounts, start=1):
                    if account:
                        address = self.generate_address(account)
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {idx} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )
                        
                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Private Key or Library Version Not Supported {Style.RESET_ALL}"
                            )
                            continue

                        self.HEADERS[address] = {
                            "Accept": "application/json, text/plain, */*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://www.dapcoin.xyz",
                            "Referer": "https://www.dapcoin.xyz/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-site",
                            "User-Agent": FakeUserAgent().random
                        }

                        await self.process_accounts(account, address, use_proxy, rotate_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*68)
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        bot = DAP()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] DAP - BOT{Style.RESET_ALL}                                       "                              
        )