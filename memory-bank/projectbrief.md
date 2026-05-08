# Project Brief: JTWMS

## Core Goal
Build a web application to centralise teacher data, automate scheduling, track utilisation, and provide workforce forecasting across **10 English language centres**.  
The system must handle a mixed workforce of full‑time (fixed salary) and part‑time (hourly pay) teachers, with a human‑in‑the‑loop approval process.

## Key Business Rules (Critical)
- **Full‑time teachers**: fixed monthly salary for a contracted number of hours. If they teach more, they receive a bonus. If they teach less (low student numbers), they still receive full salary but no bonus.  
  → Scheduling must maximise FT teacher utilisation to avoid wasted salary.
- **Part‑time teachers**: paid only for actual teaching hours at an hourly rate. No teaching = no cost.  
  → PT teachers are used only after all FT teachers are fully loaded (up to contracted hours).

## Core Modules (from the proposal)
1. Teacher Registry  
2. Class & Room Inventory  
3. Timetable Generator (constraint‑based, two‑phase: FT‑first, then PT overflow)  
4. Teacher Assignment & Workload Tracker  
5. Supply Forecasting (12‑week horizon, with idle/unavailable metrics)  
6. HR Coordination (headcount requests, vacancy tracking, contract alerts)  
7. Reporting & Analytics (KPIs as per proposal)

## Forecasting Alerts
- **Unassigned FT Rate > 50%** → trigger “cut‑off review” (too many idle FT teachers – wasted salary).  
- **Available Teacher Rate < 20%** → trigger “recruit more” (almost no spare capacity in any teacher).  
These are in addition to the gap‑based recruitment trigger (deficit > 10 hrs/wk for 3 consecutive weeks).

## Target Users
- Academic Managers (schedule, assign, approve)  
- HR Coordinators (headcount, contract management, cost reporting)  
- Centre Administrators (room inventory, basic class management)

## Constraints
- The scheduling engine must **never publish** a timetable without human approval.  
- Teacher salary details are HR‑only, not visible to Academic Managers.  
- All data exportable to CSV/XLSX for backward compatibility.