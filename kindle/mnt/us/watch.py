import os
import time
import json
import uuid
import urllib.request
import urllib.error
import subprocess
import ssl

WATCH_DIR = "/mnt/us/koreader/photo_frame/images"
BASE_URL = "https://my-kindle-subdomain.example.com"
ENDPOINT = f"{BASE_URL}/process"

POLL_INTERVAL = 3.0
MAX_RETRIES = 3
ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".heic"}
STATE_FILE = os.path.join(WATCH_DIR, ".processed_state.json")


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    tmp_state = STATE_FILE + ".tmp"
    with open(tmp_state, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp_state, STATE_FILE)


def ensure_wifi_connected():
    """Acorda o Wi-Fi do Kindle e aguarda até 10 segundos para ele obter IP/conexão."""
    try:
        subprocess.run(
            ["lipc-set-prop", "com.lab126.wifid", "enable", "1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        for _ in range(10):
            res = subprocess.run(
                ["lipc-get-prop", "com.lab126.wifid", "cmState"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if "CONNECTED" in res.stdout:
                return True
            time.sleep(1)
    except Exception:
        pass
    return False


def get_screen_state():
    """Retorna o estado atual do powerd do Kindle (ex: 'active', 'screenSaver', 'suspended')."""
    try:
        res = subprocess.run(
            ["lipc-get-prop", "com.lab126.powerd", "state"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return res.stdout.strip()
    except Exception as e:
        print(f"Erro ao ler estado da tela: {e}", flush=True)
        return ""


def press_power_button():
    """Simula um clique físico no botão power do Kindle."""
    subprocess.run(
        ["lipc-set-prop", "-i", "com.lab126.powerd", "powerButton", "1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=3,
    )


def cycle_screen_if_off():
    """
    Se a tela estiver desligada (não 'active'), simula o clique no botão power
    para acordar, aguarda 1.5s e clica novamente para desligar e carregar a nova foto.
    Se estiver ligada ('active'), não faz nada.
    """
    current_state = get_screen_state()

    if not current_state:
        print("Aviso: Não foi possível detectar o estado da tela.", flush=True)
        return

    if current_state == "active":
        print("Tela está ligada (active). Nenhuma ação necessária.", flush=True)
        return

    print(f"Tela desligada ({current_state}). Simulando clique para acordar...", flush=True)
    try:
        # 1º clique: acorda a tela
        press_power_button()
        time.sleep(1.5)

        # 2º clique: desliga a tela novamente para atualizar o screensaver
        print("Simulando segundo clique para voltar ao screensaver com a nova foto...", flush=True)
        press_power_button()
    except Exception as e:
        print(f"Erro ao simular botão power: {e}", flush=True)


def upload_and_replace(filepath, filename):
    """Envia a imagem via multipart/form-data puro e salva o retorno da API."""
    if not ensure_wifi_connected():
        raise RuntimeError("Wi-Fi do Kindle não conectou a tempo")

    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"Enviando {filename} ({file_size_mb:.2f} MB)...", flush=True)

    boundary = uuid.uuid4().hex

    with open(filepath, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(ENDPOINT, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Content-Length", str(len(body)))
    req.add_header("User-Agent", "curl/8.5.0")

    ca_file = "/etc/ssl/certs/ca-certificates.crt"
    if os.path.exists(ca_file):
        ssl_ctx = ssl.create_default_context(cafile=ca_file)
    else:
        ssl_ctx = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(req, timeout=60, context=ssl_ctx) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}")
            processed_bytes = resp.read()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code}: {err_body}")

    if not processed_bytes:
        raise RuntimeError("Resposta vazia da API")

    name_only = os.path.splitext(filename)[0]
    final_path = os.path.join(WATCH_DIR, f"{name_only}.png")
    temp_path = os.path.join(WATCH_DIR, f".{name_only}.png.tmp")

    with open(temp_path, "wb") as f:
        f.write(processed_bytes)

    os.replace(temp_path, final_path)

    if os.path.abspath(filepath) != os.path.abspath(final_path) and os.path.exists(filepath):
        os.remove(filepath)

    return final_path

def keep_system_awake():
    """
    Impede o Kindle de entrar em Deep Sleep (congelar CPU/Wi-Fi)
    mesmo quando a tela está exibindo o screensaver.
    """
    try:
        # Adia a suspensão do powerd por 300 segundos (renovado a cada 3s no loop)
        subprocess.run(
            ["lipc-set-prop", "-i", "com.lab126.powerd", "deferSuspend", "300"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        # Mantém o Wi-Fi ativo sem entrar em modo de economia extrema
        subprocess.run(
            ["lipc-set-prop", "com.lab126.wifid", "enable", "1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except Exception:
        pass

def wait_file_stable(filepath):
    """Aguarda o Syncthing terminar de gravar o arquivo antes de enviar."""
    prev_size = -1
    for _ in range(10):
        try:
            curr_size = os.path.getsize(filepath)
            if curr_size > 0 and curr_size == prev_size:
                return True
            prev_size = curr_size
        except OSError:
            return False
        time.sleep(0.5)
    return False


def main():
    print(f"Monitorando {WATCH_DIR} (API: {ENDPOINT})...", flush=True)
    state = load_state()
    fail_counts = {}

    while True:
        try:
            entries = os.listdir(WATCH_DIR)
        except OSError as e:
            print(f"Erro ao ler diretório: {e}", flush=True)
            time.sleep(POLL_INTERVAL)
            continue

        for filename in entries:
            if filename.startswith(".") or filename.endswith(".tmp"):
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ext not in ALLOWED_EXTS:
                continue

            filepath = os.path.join(WATCH_DIR, filename)
            if not os.path.isfile(filepath):
                continue

            try:
                mtime = os.path.getmtime(filepath)
            except OSError:
                continue

            if state.get(filename) == mtime:
                continue

            file_key = (filename, mtime)
            if fail_counts.get(file_key, 0) >= MAX_RETRIES:
                continue

            if not wait_file_stable(filepath):
                continue

            attempt = fail_counts.get(file_key, 0) + 1
            print(f"Processando: {filename} (tentativa {attempt}/{MAX_RETRIES})...", flush=True)

            try:
                final_path = upload_and_replace(filepath, filename)
                final_name = os.path.basename(final_path)

                state.pop(filename, None)
                state[final_name] = os.path.getmtime(final_path)
                save_state(state)
                fail_counts.pop(file_key, None)

                print(f"Concluído: {final_name}", flush=True)

                # Atualiza a tela imediatamente após cada imagem concluída
                cycle_screen_if_off()

            except Exception as e:
                fail_counts[file_key] = attempt
                print(f"Falha ao processar {filename} ({attempt}/{MAX_RETRIES}): {e}", flush=True)
                if attempt >= MAX_RETRIES:
                    print(f"Limite de tentativas atingido para {filename}. Pulando arquivo.", flush=True)
                else:
                    time.sleep(5)

        keep_system_awake()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
