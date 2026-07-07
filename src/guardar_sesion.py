from playwright.sync_api import sync_playwright
import time


def guardar_sesion_ultra_sigilo():
    print("🚀 Lanzando Chrome en modo 'Humano Indetectable'...")

    with sync_playwright() as p:
        # Usamos argumentos para desactivar la bandera de 'automation'
        contexto = p.chromium.launch_persistent_context(
            user_data_dir="../perfil_bot",
            channel="chrome",
            headless=False,
            # ESTA ES LA CLAVE: Borramos el cartel de 'automatizado'
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ],
            ignore_default_args=["--enable-automation"],
            viewport={"width": 1920, "height": 1080}
        )

        pagina = contexto.new_page()

        # Inyectamos un script extra para que navigator.webdriver sea 'false'
        pagina.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("🌐 Entrando a Betwatch...")
        pagina.goto("https://betwatch.fr/account/login")

        print("\n🆘 INSTRUCCIONES:")
        print("1. El cartelito de 'software automatizado' debería haber DESAPARECIDO.")
        print("2. Loguea normalmente. Si sale el círculo de 'Verifying', ahora debería pasar.")
        print("3. Cuando veas tus datos cargados, espera 10 segundos.")
        print("4. CIERRA EL NAVEGADOR MANUALMENTE.")

        # Bucle para mantenerlo abierto hasta que tú lo cierres
        try:
            while len(contexto.pages) > 0:
                time.sleep(1)
        except:
            pass

        print("✅ Sesión guardada. Ahora el bot podrá usar tu identidad.")


if __name__ == "__main__":
    guardar_sesion_ultra_sigilo()