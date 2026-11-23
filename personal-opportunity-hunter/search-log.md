# Search Log

## Run 1: 2026-11-23 (initial research run)

### Capabilities check

| Capability | Available? | Notes |
|---|---|---|
| Web search | Yes | Also supports restricting results to specific domains (used for official verification) |
| Opening full web pages | **No** | Page fetches failed with DNS errors, even after a "Opportunity Hunter" cloud environment allowing ~20 organiser domains was created and approved. Shell `curl` was not permitted. |
| Extracting deadlines | Partial | From official-domain search snippets |
| Saving/updating local files | Yes | Repo branch `claude/beautiful-mendel-4i4gde` |
| Scheduled searches | Possible with approval | Cloud scheduled tasks; not configured (see config.md) |

### Queries run (all "standard" web search)

Broad / per-category:
- PyCon US 2027 travel grant application
- Lindau Nobel Laureate Meeting 2027 application young scientists
- Heidelberg Laureate Forum 2027 application deadline young researchers
- KubeCon CloudNativeCon Europe 2027 dan kohn scholarship
- EuroPython 2027 financial aid grant
- Web Summit Lisbon 2026 2027 women in tech / startup free ticket ALPHA programme
- GHC 2027 Grace Hopper Celebration India scholarship / AnitaB.org
- NeurIPS 2026 / ICML 2027 financial assistance volunteer registration travel award students
- "One Young World" 2027 summit scholarship fully funded application
- St. Gallen Symposium 2027 Global Essay Competition Leaders of Tomorrow deadline
- FOSDEM 2027 dates travel support / Google Summer of Code mentor summit
- Falling Walls Lab 2027 India application finalists Berlin travel covered
- Google DeepMind / Google conference travel grant students AI 2027 India
- ETHGlobal hackathon 2027 travel stipend / international hackathon flights covered 2027
- bonding Firmenkontaktmesse Stuttgart 2027 / career fair University of Stuttgart 2027 dates
- Mozilla Festival / Linux Foundation Open Source Summit Europe 2027 travel fund application
- Young European Leaders / "fully funded" technology youth summit 2027 apply international
- ACL 2027 / EMNLP / AAAI 2027 student scholarship volunteer travel grant deadline
- Microsoft Imagine Cup 2027 registration deadline world finals travel
- ICLR 2027 financial assistance application
- Slush 2026 volunteer Helsinki / Slush student pass
- EEML 2027 summer school machine learning travel grants application
- PyCon DE PyData 2027 financial aid / WeAreDevelopers World Congress 2027 volunteer
- Citadel conference travel grant 2027 ICML ICLR application students
- AWS re:Invent 2026 All Builders Welcome Grant eligibility flights hotel
- GitHub Universe 2026 scholarship / "AI Engineer World's Fair" 2027 volunteer scholarship
- KDD 2027 student travel award / ICML 2027 financial aid dates Seoul
- Oxford Machine Learning Summer School 2027 OxML / LxMLS 2027 application scholarship
- Bits & Pretzels 2027 student ticket / Munich startup festival volunteer free *(no relevant results)*
- DAAD ... "Kongressreisen" / Stuttgart international students networking 2027 (German)
- HackZurich 2027 travel reimbursement / Junction 2026 hackathon Helsinki travel reimbursement
- WeAreDevelopers World Congress 2027 call for volunteers dates Berlin
- Grace Hopper Celebration India 2027 GHCI scholarship application deadline
- "PyCon US 2027" Long Beach dates travel grants open
- Google Summer of Code 2027 timeline / LFX mentorship / Outreachy May 2027
- Lindau Nobel Laureate Meeting 2028 / physics 2027 India nomination DST
- START Hack 2027 St. Gallen hackathon travel reimbursement application
- FOSSASIA Summit 2027 dates call for speakers volunteers travel
- EuroPython 2027 location dates announced
- IKOM München / connecticum / "Absolventenkongress" 2027 Karrieremesse Informatik (German)

Official-domain verification queries (results limited to the organiser's domain):
heidelberg-laureate-forum.org, aaai.org, pycon.de, symposium.org, imaginecup.microsoft.com, wearedevelopers.com, aws.amazon.com, citadel.com/citadelsecurities.com, events.linuxfoundation.org/cncf.io, oneyoungworld.com, iclr.cc, buildyourfuture.withgoogle.com/edu.google.com, anitab.org.

### Outcomes

- 27 active records, 8 excluded/flagged.
- Gaps to fill next run: Bits & Pretzels, VivaTech, TechCrunch Disrupt, Hugging Face / OpenAI community events, Google I/O Connect Berlin, GDG / Microsoft Learn Student Ambassadors, MLH, Junction 2027, ICML 2027 location, ACL/EMNLP 2027 grants, KDD 2027, CVPR 2027, Cyber Valley / ELLIS events in Stuttgart-Tübingen, TUM.ai Makeathon, IEEE/ACM student travel grants (SIGKDD, SIGIR), Erasmus+ / EU youth programmes, German-language queries for Stuttgart Werkstudent events.
- Re-attempt full-page verification once page fetching works.
