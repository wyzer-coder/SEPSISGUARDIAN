# DEMO SCRIPT (about 2 min 40 s)

**Before recording:** open the website, choose **English**, close other tabs, and zoom the browser to 90%.
Every number below is real (from `results/metrics.json` and the demo data).

| Time | Show (click) | Say |
|---|---|---|
| 0:00–0:15 | **Home** page, top | "Sepsis kills when it's caught late. But alarms that ring all the time get ignored. One widely used sepsis model missed 67% of patients, and only 12% of its alerts were right." |
| 0:15–0:35 | Scroll to **The three gates** table | "SepsisGuardian pages a nurse only when three gates pass: the risk is high, the patient is getting worse right now, and we haven't paged in the last 6 hours." |
| 0:35–1:00 | **Ward Overview** → drag the slider to **hour 39** | "This is a replay of 50 real ICU patients from a hospital our model never saw. At hour 39, two beds are red. Bed 20 is at the top." |
| 1:00–1:35 | **Click the Bed 20 row** → Patient Detail. Sidebar: choose **தமிழ்** | "Bed 20 developed sepsis at hour 51, and we alerted at hour 39, 12 hours early. Here's the alert in Tamil: oxygen is at 92%, and lactate hasn't been measured for 36 hours, so confidence is lower. The table on the right shows each gate passing." |
| 1:35–1:55 | Switch back to **English**, move the hour slider to **41** | "Two hours later the risk is still high, but the patient is SUPPRESSED, the grey dot. Gate 3 says we paged two hours ago, so no repeat alarm. It's logged, but the nurse isn't disturbed." |
| 1:55–2:25 | **Results** page | "On the unseen hospital, the three gates cut alerts from 544 to 76 per 100 patient-days, seven times quieter, while still warning 65% of sepsis patients before onset. To be honest, the gates make the alarm quieter, not smarter: about 1 alert in 20 is a true early warning." |
| 2:25–2:40 | Scroll to the safety line | "This is decision support, not a diagnosis. A clinician always confirms. In the final round we'll add nurse feedback buttons and a live replay." |

**Backup if the live site is slow:** use the screenshots in `docs/screenshots/` in the same order.
