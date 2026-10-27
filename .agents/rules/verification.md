---
trigger: always_on
description: "Obavezna verifikacija i materijalni dokaz pre potvrde uspeha. Zabrana mock testova i simulacija."
---

# Pravilo Verifikacije Izmena

## Obavezni uslovi pre svake potvrde uspeha

1. **Stvarni testovi:** Ne potvrđuj uspeh bez pokretanja stvarnih automatizovanih testova koji direktno pokrivaju unete izmene. Testovi ne smeju koristiti mock-ove za JudgeGuard, auth tokene, ili bezbednosne kapije.

2. **Zabrana mock-ova (Zero-Simulation Law):** Svaki test koji koristi `MagicMock`, `patch`, ili simulirane odgovore za stvarne API pozive i bezbednosne kapije je **zabranjeno koristiti kao dokaz uspeha**. Dozvoljeni su jedino pravi unit testovi logike.

3. **Pre-Action kapija:** Sve kritične operacije (pisanje datoteka, git commit, deploy) moraju proći JudgeGuard kapiju:
   ```bash
   echo "🟡 Starting [ACTION]" >> WORK_LOG.md
   python3 judge_guard.py "[ACTION]"
   # Nastavi SAMO ako je Exit Code 0
   ```

4. **Obavezni materijalni dokazi:**
   - Kompletan `git diff` ili `git status` za sve izmenjene datoteke
   - Ceo izlaz test kontrolera sa **Exit Code 0**
   - Prikaz izvršenih komandi iz audit loga

5. **Hook blokade:** Komande koje idu kroz `run_command` alat prolaze kroz `scripts/verify_command_safety.py`. Ako hook vrati Exit Code 1, izvršenje je **fizički blokirano**.

6. **MCP serveri:** `personalized-service-health` i `sequential-thinking` su konfigurisani i verifikovani. Za `personalized-service-health` — GCP projekat mora imati Service Health API odobren.
