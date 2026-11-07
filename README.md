# ai_cli

ai_cli, yazdığınız komut isteğini bir yapay zekâ modeli ile çalışabilir bir kabuk komutuna dönüştüren basit bir araçtır. Varsayılan olarak yerel [Ollama](https://ollama.com) modelleriyle çalışır; isterseniz OpenAI API'ye geçebilirsiniz. Program önerdiği komutu çalıştırmak isteyip istemediğinizi sorar ve son komutları kaydeder.

## Kurulum

1. Python 3 kurulu olmalıdır.
2. Depoyu klonlayın veya indirin.
3. Bağımlılıkları yüklemek için:
   ```bash
   pip install -r requirements.txt
   ```
4. Ollama'yı kurun ve en az bir model indirin:
   ```bash
   ollama pull qwen3:8b
   ```
   Model seçmezseniz ilk çalıştırmada kurulu ilk sohbet modeli otomatik seçilir ve `config.json`'a kaydedilir. Ollama başka bir makinede çalışıyorsa `OLLAMA_HOST` ortam değişkenini (ör. `OLLAMA_HOST=192.168.1.10:11434`) ortamınızda ya da `.env` dosyasında tanımlayın.
5. Aşağıdaki işletim sistemi için uygun kurulum betiğini çalıştırın:
   - **Windows**: `install_windows.bat`
   - **macOS**: `bash install_macos.sh`
   - **Ubuntu**: `bash install_ubuntu.sh`

Betikler `ask` komutunu doğrudan çağırabilmeniz için kullanıcı dizininizdeki `~/.local/bin` veya `%USERPROFILE%\.bin` konumuna kısayol oluşturur ve gerekli ise bu dizini PATH değişkeninize ekler. Değişikliğin etkili olması için yeni bir terminal açmanız gerekebilir.

### OpenAI kullanmak

```bash
ask set-key sk-<anahtar>
ask provider openai
```
Anahtarı doğrudan `.env` dosyasına `OPENAI_KEY=sk-<anahtar>` şeklinde de yazabilirsiniz. Tekrar Ollama'ya dönmek için `ask provider ollama`.

## Kullanım

Terminalde şu şekilde komut verebilirsiniz:
```bash
ask ~/Downloads klasöründeki tüm .png dosyalarını sil
```
Program önerdiği komutu gösterir ve çalıştırmak isteyip istemediğinizi sorar.

Bazı yardımcı komutlar:
- `ask new` – önceki mesajı ve komut geçmişini temizler.
- `ask run` – son komutu tekrar çalıştırır.
- `ask run N` – geçmişteki N numaralı komutu çalıştırır.
- `ask last` – son on komutu listeler.
- `ask provider` – kullanılan sağlayıcıyı (ollama/openai) gösterir.
- `ask provider ollama|openai` – sağlayıcıyı değiştirir.
- `ask model` – kullanılan modeli gösterir.
- `ask model MODEL_ADI` – aktif sağlayıcının modelini değiştirir (model her sağlayıcı için ayrı saklanır).
- `ask models` – mevcut modelleri listeler (Ollama'da embedding modelleri listelenmez).
- `ask set-key ANAHTAR` – OpenAI anahtarını kaydeder.

### Ortam değişkenleri

| Değişken | Açıklama |
|---|---|
| `OLLAMA_HOST` | Ollama sunucu adresi (varsayılan `http://localhost:11434`) |
| `OLLAMA_MODEL` | `config.json`'daki Ollama modelini geçersiz kılar |
| `OPENAI_KEY` | OpenAI API anahtarı |
| `ASK_PROVIDER` | `config.json`'daki sağlayıcıyı geçersiz kılar |

## Lisans

MIT Lisansı ile dağıtılmaktadır.
