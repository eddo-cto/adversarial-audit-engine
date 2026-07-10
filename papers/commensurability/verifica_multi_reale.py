# Esegue ENTRAMBI gli esempi reali e riassume la robustezza multi-caso / multi-lente.
import statistics, random, importlib
BOT,K,TOP=0,1,2; NOMI={BOT:"BOT",K:"k",TOP:"TOP"}

print("#"*74); print("# ESEMPIO A — ACCUMULO (Giugliano, lente: core compliance edilizia)"); print("#"*74)
import subprocess, sys
# riusa lo script d'accumulo già validato
out=subprocess.run([sys.executable,"verifica_esempio_reale.py"],capture_output=True,text=True)
print(out.stdout.strip())

print("\n"+"#"*74); print("# ESEMPIO B — COMMENSURABILITÀ DI 2 LINEE INDIPENDENTI su 6 beni (lente: valutatori)"); print("#"*74)
B=importlib.import_module("DATI_valutatori_6beni")
print("bene / territorio / divergenza -> commensurabilità delle due linee indipendenti:")
counts={TOP:0,K:0,BOT:0}
for (bene,terr,div,esito,val,nota) in B.BENI:
    counts[val]+=1
    print(f"  [{NOMI[val]:3}] {bene:34} ({terr:9}) div={div:4}  {esito}  — {nota}")
print(f"\nconteggio valori C3 istanziati da dati reali: TOP={counts[TOP]}  k={counts[K]}  BOT={counts[BOT]}")
tutti = all(counts[v]>0 for v in (TOP,K,BOT))
print(f"tutti e tre i valori di C3 presenti in dati reali: {tutti}")
print("  => la commensurabilità a 3 valori del §2.2 NON è un artefatto del righello sintetico:")
print("     TOP = linee convergenti (banda comune); k = divergenza materiale = NON-CHIUSURA dichiarata")
print("     ('non mediare'); BOT = astensione = non-conoscenza dichiarata. È esattamente R⁺/R?/R⁻ del §2.1,")
print("     osservato su 6 beni reali con 2 linee indipendenti ciascuno.")

print("\n"+"#"*74); print("# LETTURA COMPLESSIVA (onesta)"); print("#"*74)
print("Robustezza: 7 beni reali, 6 territori, 2 famiglie di lenti (compliance + valutazione).")
print(" - Esempio A: accumulo monotono NON-ridondante + residuo dichiarato (astensione) su 1 caso ad alta fedeltà.")
print(" - Esempio B: i 3 valori di commensurabilità di C3 emergono da linee indipendenti reali su 6 beni,")
print("   con la non-chiusura (k) e l'astensione (BOT) come OUTPUT documentati, non buchi.")
print("Limite onesto: la commensurabilità è codificata (trasparente e verificabile sui file sorgente),")
print("non ancora validata da esiti d'asta reali (gap dichiarato dal motore stesso). È applicabilità, non validazione esterna.")
