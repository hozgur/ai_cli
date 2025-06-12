# ai_cli

ai_cli, OpenAI API kullanarak yazdığınız komut isteğini uygun şekilde çalışabilir bir kabuk komutuna dönüştüren basit bir aracıdır. Program önerdiği komutu çalıştırmak isteyip istemediğinizi sorar ve son komutları kaydeder.

## Kurulum

1. Python 3 kurulu olmalıdır.
2. Depoyu klonlayın veya indirin.
3. Bağımlılıkları yüklemek için:
   ```bash
   pip install -r requirements.txt
   ```
4. `.env` dosyası oluşturun ve OpenAI anahtarını girin ya da sonradan `ask set-key ANAHTAR` komutu ile de kaydedebilirsiniz :
   ```
   OPENAI_KEY=sk-<anahtar>
   ```
5. Aşağıdaki işletim sistemi için uygun kurulum betiğini çalıştırın:
   - **Windows**: `install_windows.bat`
   - **macOS**: `bash install_macos.sh`
   - **Ubuntu**: `bash install_ubuntu.sh`

Betikler `ask` komutunu doğrudan çağırabilmeniz için kullanıcı dizininizdeki `~/.local/bin` veya `%USERPROFILE%\.bin` konumuna kısayol oluşturur ve gerekli ise bu dizini PATH değişkeninize ekler. Değişikliğin etkili olması için yeni bir terminal açmanız gerekebilir.

## Kullanım

Terminalde şu şekilde komut verebilirsiniz:
```bash
ask ~/Downloads klasöründeki tüm .png dosyalarını sil
```
Program önerdiği komutu gösterir ve çalıştırmak isteyip istemediğinizi sorar.

Bazı yardımcı komutlar:
- `ask new` – önceki geçmişi temizler.
- `ask run` – son komutu tekrar çalıştırır.
- `ask last` – son on komutu listeler.
- `ask model` – kullanılan modeli gösterir.
- `ask models` – mevcut modelleri listeler.
- `ask --model MODEL_ADI` – modeli değiştirir.
- `ask set-key ANAHTAR` – OpenAI anahtarını kaydeder.

## Lisans

MIT Lisansı ile dağıtılmaktadır.
