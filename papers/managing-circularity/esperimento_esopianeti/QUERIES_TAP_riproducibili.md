# Query riproducibili — tutti i bracci (aperte, HTTP puro)
## Arm 1 — esopianeti (NASA TAP → CSV): https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=...&format=csv
select koi_disposition,count(*) from cumulative group by koi_disposition
select koi_disposition,avg(koi_score),count(*) from cumulative group by koi_disposition
select koi_fpflag_nt,koi_fpflag_ss,koi_fpflag_co,koi_fpflag_ec,koi_disposition,count(*) from cumulative group by (le 5)
select c.koi_fpflag_nt,c.koi_fpflag_ss,c.koi_fpflag_co,c.koi_fpflag_ec,count(*) from cumulative c,ps p where c.kepler_name=p.pl_name and p.pl_bmassprov='Mass' and p.default_flag=1 group by (i 4 flag)
## Arm 2 — ClinVar (NCBI eutils): https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=clinvar&term=...&retmode=json
term="criteria provided, multiple submitters, no conflicts"[Review Status]   (e gli altri stati)
term="criteria provided, conflicting classifications"[Review Status]
## Arm 3 — NVD (REST 2.0): https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate=...&pubEndDate=...&resultsPerPage=40
(estrai vulnStatus + metrics.type Primary/Secondary baseSeverity; disaccordo = severità Primary != Secondary)
