import logging
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT = 5


class ConnectivityChecker:
    def __init__(self, urls, timeout=DEFAULT_TIMEOUT, logger=None):
        self.urls = urls
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)

    def _is_ssl_fatal_error(self, error):
        """判断是否为致命SSL错误（浏览器会阻断的情况）"""
        fatal_keywords = [
            "certificate_verify_failed",
            "hostname '",
            "common name",
            "self signed certificate",
            "certific",
            "hsts",
            "err_cert_common_name_invalid",
        ]
        reason_str = str(error).lower()
        return any(k in reason_str for k in fatal_keywords)

    def _is_ssl_related_error(self, error):
        """判断是否为SSL相关错误（表示连通但SSL问题）"""
        if isinstance(error, ssl.SSLError):
            return True
        if isinstance(error, URLError) and hasattr(error, "reason"):
            reason_str = str(error.reason).lower()
            ssl_keywords = ["handshake", "ssl", "certificate", "tls"]
            return any(keyword in reason_str for keyword in ssl_keywords)
        return False

    def _check_url(self, url):
        """检测单个URL连通性"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Connection": "close",
        }

        method = "HEAD" if "generate_204" in url else "GET"

        try:
            req = Request(url, headers=headers, method=method)
            ctx = ssl.create_default_context()

            # 添加替代 CA 或关闭校验调试用途（可选）
            # ctx.load_verify_locations(cafile="/path/to/custom-ca.pem")
            # ctx.load_verify_locations(cafile="/home/sinspire/test.pem")

            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED

            with urlopen(req, timeout=self.timeout, context=ctx) as resp:
                status = resp.getcode()
                if "generate_204" in url:
                    if status == 204:
                        self.logger.info(f"\u2713 {url} - 204 No Content")
                    else:
                        self.logger.warning(f"\u2717 {url} - 非预期状态码: {status}")
                        return False
                else:
                    if status != 200:
                        self.logger.warning(f"\u2717 {url} - 非200状态码: {status}")
                        return False
                    self.logger.info(f"\u2713 {url} - {resp.getcode()}")
                return True

        except HTTPError as e:
            self.logger.info(f"\u2713 {url} - HTTP {e.code} (连通)")
            return True

        except (URLError, ssl.SSLError) as e:
            if self._is_ssl_fatal_error(e):
                self.logger.warning(f"\u2717 {url} - 致命SSL错误: {e}")
                return False
            if self._is_ssl_related_error(e):
                self.logger.info(f"\u2713 {url} - SSL错误但连通: {e}")
                return True
            self.logger.warning(f"\u2717 {url} - 底层错误: {type(e).__name__}: {e}")
            return False

        except Exception as e:
            self.logger.error(f"\u2717 {url} - 未知错误: {type(e).__name__}: {e}")
            return False

    def check_all(self):
        results = {}
        with ThreadPoolExecutor(max_workers=min(10, len(self.urls))) as executor:
            future_to_url = {
                executor.submit(self._check_url, url): url for url in self.urls
            }
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    self.logger.error(f"\u2717 {url} - 任务异常: {e}")
                    results[url] = False
        return results


def check_connectivity(urls=None, timeout=DEFAULT_TIMEOUT, logger=None, args=None):
    if urls is None:
        urls = [
            "https://www.gstatic.com/generate_204",
            "https://www.google.com/generate_204",
            "https://www.whatsapp.com/",
            "https://www.github.com/",
        ]
    if args.only_check_tiktok:
        logger.info("仅检查 TikTok 连通性")
        urls = [
            "https://www.tiktok.com/",
            "https://www.gstatic.com/generate_204",
        ]
    checker = ConnectivityChecker(urls, timeout, logger)
    results = checker.check_all()
    return all(results.values())


def main():
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    urls = [
        "https://www.gstatic.com/generate_204",
        "https://www.google.com/generate_204",
        "https://www.whatsapp.com/",
        "https://www.github.com/",
        "https://www.facebook.com/",
        "https://www.youtube.com/",
        "https://www.google.com/",
        "https://www.tiktok.com/"
    ]

    checker = ConnectivityChecker(urls)
    results = checker.check_all()

    success_count = sum(results.values())
    total_count = len(results)

    print(f"\n检测结果: {success_count}/{total_count} 个站点可达")
    if success_count == total_count:
        print("\n\033[32m\u2713 网络环境良好！\033[0m")
    else:
        for url, reachable in results.items():
            if reachable:
                print(f"  \u2713 {url}")
        for url, reachable in results.items():
            if not reachable:
                print(f"  \u2717 {url}")
        print("\n\033[33m\u26a0 网络环境存在问题\033[0m")


if __name__ == "__main__":
    main()
