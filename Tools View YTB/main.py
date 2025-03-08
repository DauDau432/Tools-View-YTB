import time
import os
import sys
import requests
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import random
from urllib3.exceptions import InsecureRequestWarning

# Tắt cảnh báo SSL không an toàn khi kiểm tra proxy
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# API configuration
PROXY_API_URL = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=1000&country=all&ssl=all&anonymity=all"
DEFAULT_PROXY_FILENAME = "proxy_list.txt"  # Tên file mặc định để lưu proxy từ API
DEFAULT_VIEW_COUNT_FILENAME = "luong_xem.txt"  # Tên file mặc định để lưu số lượng xem
TEST_URL = "https://www.youtube.com"  # URL để kiểm tra proxy có hỗ trợ HTTPS
MAX_TIMEOUT = 5  # Thời gian tối đa chờ khi kiểm tra proxy (giây)

# Biến toàn cục để đồng bộ hóa giữa các luồng
view_count_lock = threading.Lock()
running = True
total_view_count = 0  # Bắt đầu từ 0 trong mỗi lần chạy mới

def clear_screen():
    """Clear the terminal screen based on OS."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Display the program banner with animation."""
    banner = """
    ╔═══════════════════════════╗
    ║          Đậu Đậu          ║
    ╚═══════════════════════════╝
    """
    
    for char in banner:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.005)

def get_user_configuration():
    """Get user configuration for the tool."""
    display_banner()
    print(" -----------------------------------------------------------")
    print("    Nhập sai bấm (Ctrl+c+Enter) để nhập lại")
    print("    -----------------------------------------------------------")
    print("    Nếu nhập sai định dạng tools lỗi (chỉ nhập số)")
    
    try:
        # Tùy chọn cho file video
        video_filename = input("    Nhập tên file chứa danh sách URL video (mặc định: list_url_video.txt): ")
        if not video_filename:
            video_filename = "list_url_video.txt"
        
        window_count = int(input("    Nhập số instance Chrome: "))
        view_time = int(input("    Nhập thời gian xem (giây): "))
        
        # Add randomization to view time to appear more natural
        random_factor = input("    Thêm độ ngẫu nhiên cho thời gian xem? (y/n): ").lower() == 'y'
        
        # Thêm tùy chọn sử dụng proxy
        use_proxy = input("    Sử dụng proxy? (y/n): ").lower() == 'y'
        
        proxy_source = None
        proxy_filename = None
        
        if use_proxy:
            print("\n    Nguồn proxy:")
            print("    1. Sử dụng file proxy có sẵn")
            print("    2. Tải proxy từ API")
            proxy_choice = input("    Chọn (1/2): ")
            
            if proxy_choice == "1":
                proxy_source = "file"
                proxy_filename = input("    Nhập tên file chứa danh sách proxy: ")
            elif proxy_choice == "2":
                proxy_source = "api"
                # Tự động tạo tên file proxy khi sử dụng API
                proxy_filename = DEFAULT_PROXY_FILENAME
                print(f"    Proxy sẽ được tải và lưu vào file {proxy_filename}")
            else:
                print("    Lựa chọn không hợp lệ. Sử dụng file có sẵn.")
                proxy_source = "file"
                proxy_filename = input("    Nhập tên file chứa danh sách proxy: ")
        
        print("    Tools Start...")
        time.sleep(3)
        clear_screen()
        
        return {
            "video_filename": video_filename,
            "window_count": window_count,
            "view_time": view_time,
            "random_factor": random_factor,
            "use_proxy": use_proxy,
            "proxy_source": proxy_source,
            "proxy_filename": proxy_filename
        }
    except ValueError:
        print("    Lỗi: Vui lòng chỉ nhập số.")
        time.sleep(3)
        return get_user_configuration()

def load_video_list(filename):
    """Load video URLs from file."""
    try:
        with open(filename, 'r') as file:
            videos = [line.strip() for line in file.readlines() if line.strip()]
        
        if not videos:
            print(f"Danh sách video trong file {filename} trống. Vui lòng kiểm tra file.")
            sys.exit(1)
            
        return videos
    except FileNotFoundError:
        print(f"Không tìm thấy file {filename}. Vui lòng tạo file và thêm các URL video.")
        sys.exit(1)

def load_proxy_list_from_file(filename):
    """Load proxy list from file."""
    try:
        with open(filename, 'r') as file:
            proxies = [line.strip() for line in file.readlines() if line.strip()]
        
        if not proxies:
            print(f"Danh sách proxy trong file {filename} trống.")
            return []
            
        print(f"Đã tải {len(proxies)} proxy từ file {filename}.")
        return proxies
    except FileNotFoundError:
        print(f"Không tìm thấy file {filename}.")
        return []

def load_proxy_list_from_api(save_filename):
    """Load proxy list from API."""
    try:
        response = requests.get(PROXY_API_URL)
        if response.status_code == 200:
            proxies = [line.strip() for line in response.text.splitlines() if line.strip()]
            if not proxies:
                print("API trả về danh sách proxy trống.")
                return []
                
            print(f"Đã tải {len(proxies)} proxy từ API.")
            
            # Lưu danh sách proxy vào file để sử dụng sau này
            with open(save_filename, 'w') as file:
                for proxy in proxies:
                    file.write(f"{proxy}\n")
            
            print(f"Đã lưu danh sách proxy vào file {save_filename}")
            return proxies
        else:
            print(f"Lỗi khi tải proxy từ API: {response.status_code}")
            return []
    except Exception as e:
        print(f"Không thể kết nối đến API proxy: {e}")
        return []

def test_proxy(proxy):
    """Test if proxy supports HTTPS and has acceptable timeout."""
    start_time = time.time()
    try:
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        # Kiểm tra với YouTube thực tế để đảm bảo proxy hoạt động tốt với YouTube
        response = requests.get(TEST_URL, proxies=proxies, timeout=MAX_TIMEOUT, verify=False)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"Proxy hợp lệ: {proxy} (Thời gian phản hồi: {elapsed_time:.2f}s)")
            return True
        else:
            print(f"Proxy không hợp lệ: {proxy} - Mã trạng thái: {response.status_code}")
            return False
    except requests.exceptions.ConnectTimeout:
        print(f"Proxy quá chậm: {proxy} - Vượt quá {MAX_TIMEOUT}s")
        return False
    except requests.exceptions.ProxyError:
        print(f"Lỗi kết nối tới proxy: {proxy}")
        return False
    except requests.exceptions.SSLError:
        print(f"Proxy không hỗ trợ SSL: {proxy}")
        return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra proxy {proxy}: {e}")
        return False

def get_working_proxies(proxy_list):
    """Kiểm tra và trả về proxy đầu tiên hoạt động."""
    if not proxy_list:
        return []
    
    print(f"Kiểm tra danh sách proxy cho đến khi tìm thấy proxy hợp lệ...")
    
    for i, proxy in enumerate(proxy_list):
        print(f"Kiểm tra proxy {i+1}/{len(proxy_list)}: {proxy}")
        
        if test_proxy(proxy):
            print(f"Đã tìm thấy proxy hợp lệ: {proxy}")
            # Lưu proxy hợp lệ vào file
            with open("valid_proxies.txt", "w") as file:
                file.write(f"{proxy}\n")
            return [proxy]  # Trả về list chỉ chứa proxy đầu tiên hợp lệ
    
    print("Không tìm thấy proxy nào hoạt động.")
    return []  # Không tìm thấy proxy nào hợp lệ

def save_view_count(count, filename=DEFAULT_VIEW_COUNT_FILENAME):
    """Save current view count to file."""
    with open(filename, 'w') as file:
        file.write(str(count))

def create_browser(proxy=None):
    """Create and configure browser instance."""
    options = Options()
    options.add_argument("--mute-audio")  # Mute audio
    
    # Add user agent to appear more like a regular browser
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Disable automation flags to avoid detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Add proxy if specified
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    
    return webdriver.Chrome(options=options)

def browser_worker(video_list, proxy, view_time, random_factor, worker_id):
    """Worker function for each browser instance."""
    global total_view_count, running
    
    print(f"Worker {worker_id}: Khởi tạo với proxy {proxy}")
    
    # Tạo instance browser mới
    try:
        browser = create_browser(proxy)
    except Exception as e:
        print(f"Worker {worker_id}: Lỗi khi khởi tạo browser: {e}")
        return
    
    # Lặp lại liên tục qua danh sách video cho đến khi bị dừng
    video_index = worker_id % len(video_list)  # Mỗi worker bắt đầu với một video khác nhau
    
    try:
        while running:
            # Lấy URL video hiện tại
            video_url = video_list[video_index]
            
            try:
                # Mở video
                print(f"Worker {worker_id}: Mở video {video_url}")
                browser.get(video_url)
                time.sleep(7)  # Tăng thời gian chờ để đảm bảo trang tải hoàn toàn
                
                # Thử bấm nút play bằng JavaScript
                try:
                    browser.execute_script("""
                        // Cố gắng click vào nút play
                        var buttons = document.getElementsByClassName('ytp-large-play-button');
                        if (buttons.length > 0) {
                            buttons[0].click();
                        }
                        
                        // Tự động bỏ qua quảng cáo nếu có
                        var skipButtons = document.getElementsByClassName('ytp-ad-skip-button');
                        if (skipButtons.length > 0) {
                            skipButtons[0].click();
                        }
                        
                        // Tự động bỏ qua các xác nhận (verify)
                        var verifyButtons = document.querySelectorAll('button[aria-label="I am not a robot"]');
                        if (verifyButtons.length > 0) {
                            verifyButtons[0].click();
                        }
                    """)
                except Exception as e:
                    print(f"Worker {worker_id}: Không thể click button: {e}, nhưng vẫn tiếp tục xem")
                
                # Kiểm tra xem video có đang phát không
                try:
                    is_playing = browser.execute_script("""
                        var video = document.querySelector('video');
                        return video && !video.paused && !video.ended && video.readyState > 2;
                    """)
                    
                    if not is_playing:
                        print(f"Worker {worker_id}: Video không tự động phát, cố gắng phát thủ công")
                        # Thử phát thủ công bằng cách nhấn space
                        body = browser.find_element(By.TAG_NAME, "body")
                        body.send_keys(" ")
                except Exception as e:
                    print(f"Worker {worker_id}: Không thể kiểm tra trạng thái phát: {e}")
                
                # Tính toán thời gian xem
                if random_factor:
                    actual_view_time = view_time + random.randint(-min(10, view_time // 4), 10)
                    actual_view_time = max(5, actual_view_time)  # Đảm bảo tối thiểu 5 giây
                else:
                    actual_view_time = view_time
                
                print(f"Worker {worker_id}: Xem video trong {actual_view_time} giây")
                
                # Chờ trong thời gian xem
                progress_interval = min(10, actual_view_time // 5)  # Hiển thị tiến trình mỗi 10 giây hoặc ít hơn
                time_watched = 0
                
                while time_watched < actual_view_time and running:
                    wait_time = min(progress_interval, actual_view_time - time_watched)
                    time.sleep(wait_time)
                    time_watched += wait_time
                    print(f"Worker {worker_id}: Đã xem {time_watched}/{actual_view_time} giây")
                    
                    # Kiểm tra xem video còn đang phát không
                    try:
                        is_still_playing = browser.execute_script("""
                            var video = document.querySelector('video');
                            return video && !video.paused && !video.ended;
                        """)
                        
                        if not is_still_playing:
                            print(f"Worker {worker_id}: Video đã dừng, cố gắng phát lại")
                            browser.find_element(By.TAG_NAME, "body").send_keys(" ")
                    except Exception:
                        # Bỏ qua lỗi này và tiếp tục
                        pass
                    
                    # Tự động bỏ qua quảng cáo nếu có
                    try:
                        browser.execute_script("""
                            var skipButtons = document.getElementsByClassName('ytp-ad-skip-button');
                            if (skipButtons.length > 0) {
                                skipButtons[0].click();
                            }
                        """)
                    except Exception:
                        # Bỏ qua lỗi này và tiếp tục
                        pass
                
                # Tăng số lượng view
                with view_count_lock:
                    global total_view_count
                    total_view_count += 1
                    save_view_count(total_view_count)
                    print(f"Worker {worker_id}: Hoàn thành video. Tổng số lượt xem: {total_view_count}")
                
                # Chuyển sang video tiếp theo trong danh sách
                video_index = (video_index + 1) % len(video_list)
                
            except Exception as e:
                print(f"Worker {worker_id}: Lỗi khi xem video: {e}")
                # Chuyển sang video tiếp theo nếu gặp lỗi
                video_index = (video_index + 1) % len(video_list)
                time.sleep(2)  # Đợi một chút trước khi thử video khác
        
    except Exception as e:
        print(f"Worker {worker_id}: Lỗi không xử lý được: {e}")
    finally:
        # Đóng browser
        try:
            browser.quit()
        except:
            pass
        print(f"Worker {worker_id}: Đã dừng")

def manage_browser_workers(video_list, working_proxies, config):
    """Quản lý các worker cho mỗi instance browser."""
    global total_view_count, running
    
    # Luôn bắt đầu từ 0 mỗi lần chạy
    total_view_count = 0
    print(f"Bắt đầu mới với số lượng view: {total_view_count}")
    
    # Tạo danh sách worker
    workers = []
    
    try:
        # Khởi tạo số lượng worker bằng số Chrome instance được yêu cầu
        for i in range(config['window_count']):
            # Lấy proxy từ danh sách, nếu có
            proxy = None
            if working_proxies:
                proxy = working_proxies[i % len(working_proxies)]
            
            # Tạo và khởi động worker thread
            worker = threading.Thread(target=browser_worker, 
                                    args=(video_list, proxy, config['view_time'], 
                                        config['random_factor'], i))
            workers.append(worker)
            worker.start()
        
        # Vòng lặp chính - cho phép người dùng dừng chương trình bằng Ctrl+C
        print("\nĐang chạy... Nhấn Ctrl+C để dừng\n")
        try:
            while running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nNhận tín hiệu dừng từ người dùng. Đang dừng các worker...")
            running = False
            
        # Chờ tất cả worker dừng
        for worker in workers:
            worker.join()
        
        print(f"Tất cả worker đã dừng. Tổng số lượt xem: {total_view_count}")
        
    except Exception as e:
        print(f"Lỗi khi quản lý workers: {e}")
        running = False
        
        # Chờ tất cả worker dừng
        for worker in workers:
            worker.join()

def main():
    """Main program execution."""
    global running
    
    # Lấy cấu hình người dùng
    config = get_user_configuration()
    
    # Tải danh sách video
    video_list = load_video_list(config['video_filename'])
    
    # Tải danh sách proxy nếu cần
    proxy_list = []
    if config['use_proxy'] and config['proxy_source'] and config['proxy_filename']:
        if config['proxy_source'] == "file":
            proxy_list = load_proxy_list_from_file(config['proxy_filename'])
        elif config['proxy_source'] == "api":
            proxy_list = load_proxy_list_from_api(config['proxy_filename'])
        
        if not proxy_list:
            print("Không có proxy nào khả dụng. Tiếp tục không sử dụng proxy.")
            config['use_proxy'] = False
    
    # Lấy danh sách proxy hoạt động
    working_proxies = []
    if proxy_list:
        # Kiểm tra danh sách proxy cho đến khi tìm thấy proxy đầu tiên hoạt động
        working_proxies = get_working_proxies(proxy_list)
        
        if not working_proxies:
            print("Không tìm thấy proxy nào hoạt động.")
            # Chỉ hỏi người dùng khi không tìm thấy proxy nào hoạt động
            if input("Tiếp tục không sử dụng proxy? (y/n): ").lower() != 'y':
                print("Hủy bỏ.")
                return
            config['use_proxy'] = False
    
    # Hiển thị thông tin cấu hình
    print(f"  INSTANCES: {config['window_count']}")
    print(f"  VIDEO: {len(video_list)}")
    print(f"  FILE VIDEO: {config['video_filename']}")
    if working_proxies:
        print(f"  PROXIES (hoạt động): {len(working_proxies)}")
        print(f"  FILE PROXY: {config['proxy_filename']}")
    
    # Chạy quản lý các browser worker - không hỏi nữa, bắt đầu ngay
    try:
        # Thiết lập để có thể dừng bằng Ctrl+C
        running = True
        
        # Bắt đầu quản lý các worker
        manage_browser_workers(video_list, working_proxies, config)
        
    except Exception as e:
        print(f"Lỗi không xử lý được: {e}")
    finally:
        running = False
        print("Chương trình kết thúc.")

if __name__ == "__main__":
    main()