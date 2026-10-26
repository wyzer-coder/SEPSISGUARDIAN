# LEARNING AND Q&A

## The 5 key concepts (simple words)
1. **Leakage** — the model secretly sees information it would not have at that moment
   (for example, tomorrow's blood test). Scores look great in testing, then fail in a real ward.
   We prevent it by using only the past hours of the same patient, and we test this.
2. **Calibration** — when the model says "5% risk", about 5 in 100 such hours really are sepsis.
   A nurse can trust the number itself, not just the ranking. We use isotonic calibration.
3. **PPV vs sensitivity** — *Sensitivity:* of all sepsis patients, how many did we warn in time? (ours: 64.8%)
   *PPV:* of all pages to the nurse, how many were real? (ours: 5.1%). Raising one usually lowers the other.
4. **The three gates** — risk high? → getting worse now? → not paged in the last 6 h? Only then page the nurse.
   Result on hospital B: 7.2× fewer alerts (544.5 → 76.1 per 100 patient-days), 64.8% of sepsis patients caught.
5. **Train on A, test on B** — we learn and choose the threshold on hospital A only.
   Hospital B is a different hospital, kept locked until the final test.
   This shows whether the model still works in a hospital it has never seen.

## Learning list (≤ 4 hours)
| Time | What | How |
|---|---|---|
| 30 min | What sepsis is and why early warning matters | Read the README "Problem" + Singer 2016 abstract (Sepsis-3) |
| 30 min | Our data and leakage | `docs/DATA_AND_MODEL.md`: Dataset, Labels, Leakage rules |
| 45 min | **The three gates (most important)** | Read `src/gates.py` top to bottom; run `.venv/bin/pytest tests/test_gates.py -v` and read each test name |
| 30 min | PPV, sensitivity, AUROC in plain words | `docs/DATA_AND_MODEL.md` metric table + the Results page "What these words mean" |
| 30 min | Our real results and their limits | Results page + "Honest reading" in the README |
| 45 min | Practise the 15 questions below **out loud** | Answer without looking, then compare |
| 30 min | Rehearse the demo | `docs/DEMO_SCRIPT.md` with the live website |

## Judge questions with model answers
_Say them in your own words. Short and clear is best._

**Q1. Your model gives a risk score. Why not just alert whenever risk is high?**
Because a sick patient stays "high risk" for many hours. A simple rule would page the nurse
every hour, and most of those pages add nothing new. Too many alarms make nurses ignore all of
them ("alert fatigue"). So we also require that the patient is getting worse *now* (Gate 2)
and that we haven't already alerted in the last 6 hours (Gate 3).

**Q2. Why "decision support, not diagnosis"?**
A diagnosis is a doctor's decision that the patient has sepsis, and it decides treatment.
Our tool only says "this patient needs a look now, and here's why". A clinician always
checks and decides. Our thresholds are also not clinically validated, so claiming
diagnosis would be unsafe and untrue.

**Q3. Why train on hospital A and test on hospital B instead of mixing everyone?**
A real hospital that adopts our tool will be a *new* hospital, with different machines,
habits and patients. Testing on a hospital the model never saw shows honestly whether it
travels. Mixing would let the model learn hospital-specific quirks and look better than it is.

**Q4. What is leakage, and how do you prevent it?**
Leakage is when the model uses information from the future or from the answer.
We build each hour's features only from that hour and earlier hours of the same patient.
We split hospital A by patient, not by row. A test changes the future hours and checks
that today's features don't change.

**Q5. Why forward-fill per patient, and never backward?**
A lab like lactate is measured only every few hours. Between tests, the nurse assumes the last
value still holds, so we do the same. Per patient: otherwise patient 2 would inherit patient 1's
blood test. Never backward: that would copy a *future* test result into the past (leakage).
We also keep a "missing" flag and "hours since last test", so the model knows the value is old.

**Q6. Explain each of your three gates.**
Gate 1: is the risk at least 1.8%? If not, green, no alert. Gate 2: is the patient getting worse now? MAP fell
10 or more, heart rate rose 15 or more, lactate rose 0.5 or more, breathing ≥ 24, or oxygen ≤ 92%. If not, yellow
"watch", no page. Gate 3: did we page in the last 6 hours? If yes, grey "suppressed", logged but no page.
All three pass: red "review", the nurse is paged.

**Q7. What does PPV mean, and why is yours only 5%?**
PPV = of all pages, how many were real early warnings. 5% means about 1 in 20. Sepsis is rare (about 2% of hours),
and our model is modest (AUROC 0.74). The gates cut the *number* of pages 7×, but they don't make each page much
more accurate. Honest answer: this is a prototype; better features and more data are the next step.

**Q8. Your baseline scored higher than your main model on hospital B. Why didn't you switch?**
We picked the model on hospital A's validation data, where the main model won. Switching after looking at B would
be choosing on the test set, so B would no longer be an honest test. We report both.

**Q9. Why is your threshold only 0.018 (1.8%)?**
Risks are calibrated, so they're small: only about 2% of hours are sepsis hours. 0.018 is the setting that kept
≥ 60% of validation sepsis patients caught with the gates on, at the best PPV. It was chosen on hospital A only.

**Q10. Did you use AI tools?**
Yes, openly. Claude (an AI assistant) helped write the code and docs, including `gates.py` (at our request).
We chose the problem and the three-gate idea, reviewed every file, ran every test, and can explain every line.

**Q11. Is this beyond a first-year's level?**
The ideas are simple: compare trends over 3 hours, apply three yes/no rules, measure how often we're right.
The tools (pandas, scikit-learn, Streamlit) are standard. We used AI help openly for the code, and we can
explain every part: what goes in, what comes out, and why. The innovation is the alert *policy*, not complex maths.

**Q12. Why fixed sentences instead of Google Translate?**
Medical safety: the same words every time, checked by a person, no surprises, and it works offline.
Machine translation can change meaning, and a wrong word in an alert could mislead a nurse.

**Q13. What does "Lactate not measured for 36 hours" tell the nurse?**
That our risk is based on old information, so trust it less. It also suggests ordering a lactate test.
We never invent a value for a test that wasn't done.

**Q14. How do you know your demo isn't cherry-picked?**
The 15 sepsis patients on the website were chosen at random (seed 42) from the unseen hospital, so some are
missed cases. The headline numbers come from all 2,000 hospital-B patients, not from the demo.

**Q15. What would you build next (final round)?**
Nurse "Reviewed / False alarm" buttons that feed Gate 3, a live hour-by-hour replay, a fairness check by age and
sex, and spoken alerts. Longer term: richer features and a real prospective study with a hospital.
