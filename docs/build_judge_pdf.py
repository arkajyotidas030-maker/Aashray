"""Build the judge presentation brief from the implemented prototype."""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent / "AASHRAY_Judge_Presentation.pdf"
FONT = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONTB = Path(r"C:\Windows\Fonts\segoeuib.ttf")

NAVY = (15, 45, 92)
TEAL = (19, 78, 74)
INK = (20, 32, 28)
MUTED = (70, 80, 78)
RULE = (210, 206, 196)


class Brief(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 12, "F")
        self.set_font("Segoe", "", 9)
        self.set_text_color(255, 255, 255)
        self.set_xy(14, 3.5)
        self.cell(120, 5, "AASHRAY  ·  Judge presentation brief")
        self.set_xy(140, 3.5)
        self.cell(56, 5, "VBYLD  ·  Hack for Social Cause", align="R")
        self.set_text_color(*INK)
        self.set_y(18)

    def footer(self):
        self.set_y(-12)
        self.set_draw_color(*RULE)
        self.line(14, self.get_y(), 196, self.get_y())
        self.set_font("Segoe", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, "Student prototype. Not official NDMA / SDRF / 112 software.    " + str(self.page_no()), align="R")
        self.set_text_color(*INK)

    def h1(self, text: str):
        self.set_x(14)
        self.ln(2)
        self.set_font("Segoe", "B", 16)
        self.set_text_color(*NAVY)
        self.multi_cell(182, 8, text)
        self.set_draw_color(*TEAL)
        self.set_line_width(0.6)
        self.line(14, self.get_y() + 1, 70, self.get_y() + 1)
        self.ln(4)
        self.set_text_color(*INK)
        self.set_line_width(0.2)

    def h2(self, text: str):
        self.set_x(14)
        self.ln(2)
        self.set_font("Segoe", "B", 12.5)
        self.set_text_color(*TEAL)
        self.multi_cell(182, 7, text)
        self.ln(1)
        self.set_text_color(*INK)

    def p(self, text: str):
        self.set_x(14)
        self.set_font("Segoe", "", 10.5)
        self.set_text_color(*INK)
        self.multi_cell(182, 5.6, text)
        self.ln(1.5)

    def bullet(self, text: str):
        self.set_x(18)
        self.set_font("Segoe", "", 10.5)
        self.set_text_color(*INK)
        self.multi_cell(178, 5.6, "-  " + text)
        self.ln(0.4)

    def qa(self, q: str, a: str):
        if self.get_y() > 250:
            self.add_page()
        self.set_x(14)
        self.set_font("Segoe", "B", 10.5)
        self.set_text_color(*NAVY)
        self.multi_cell(182, 5.6, "Q.  " + q)
        self.set_x(14)
        self.set_font("Segoe", "", 10.5)
        self.set_text_color(*INK)
        self.multi_cell(182, 5.6, "A.  " + a)
        self.ln(2.2)

    def row(self, left: str, right: str):
        y = self.get_y()
        if y > 265:
            self.add_page()
            y = self.get_y()
        self.set_font("Segoe", "B", 10)
        self.set_xy(14, y)
        self.multi_cell(52, 5.4, left)
        h = self.get_y() - y
        self.set_font("Segoe", "", 10)
        self.set_xy(68, y)
        self.multi_cell(128, 5.4, right)
        h2 = self.get_y() - y
        self.set_xy(14, y + max(h, h2) + 1.2)


def build() -> None:
    pdf = Brief(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_font("Segoe", "", str(FONT))
    pdf.add_font("Segoe", "B", str(FONTB))
    pdf.set_margins(14, 16, 14)

    # Cover
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 78, "F")
    pdf.set_xy(14, 22)
    pdf.set_font("Segoe", "", 11)
    pdf.set_text_color(180, 205, 230)
    pdf.cell(0, 6, "VIKSIT BHARAT YOUNG LEADERS DIALOGUE")
    pdf.set_xy(14, 30)
    pdf.set_font("Segoe", "B", 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "AASHRAY")
    pdf.set_xy(14, 44)
    pdf.set_font("Segoe", "", 13)
    pdf.set_text_color(220, 230, 240)
    pdf.multi_cell(170, 7, "How we present this prototype to a national hackathon jury,\nand how we answer the hard questions.")
    pdf.set_xy(14, 66)
    pdf.set_font("Segoe", "", 10)
    pdf.set_text_color(170, 190, 210)
    pdf.cell(0, 6, "September 2026  ·  Hack for Social Cause  ·  Matches the code that actually runs")

    pdf.set_text_color(*INK)
    pdf.set_y(90)
    pdf.h2("How to use this brief")
    pdf.p(
        "Read section 2 aloud as the opening. Walk section 4 on the laptop without skipping ahead. "
        "When a judge interrupts, answer from section 7 in one or two sentences, then offer to show the screen. "
        "Never upgrade a simulated layer into a live government feed while you are talking."
    )
    pdf.h2("The only sentence that must be true")
    pdf.p(
        "AASHRAY is a student situation-awareness prototype for one hill-district landslide. "
        "It fuses citizen reports into incidents, shows where the picture is still incomplete, "
        "and still runs when the language model is off. It is not official disaster-management software."
    )

    pdf.add_page()
    pdf.h1("1. What we are showing, and what we refuse to show")
    pdf.p(
        "Judges have seen many SOS buttons on a map. The difference we defend is the object on the screen: "
        "an incident with members, a confidence score, a reason the fast road was rejected, and an honest gap "
        "where people have not checked in. Silence is not a missing-person count."
    )
    pdf.h2("Say this")
    for line in [
        "Evidence is not an incident. Nearby reports can fuse into one cluster.",
        "Cluster confidence is a fusion score, not field-validated accuracy.",
        "One SOS cannot raise a Critical alert. A second signal, or SOS plus the demo rainfall, can.",
        "Isolation means the last scripted road to Gahar hamlet is cut, computed by graph search, not by pin distance.",
        "The fast valley road is rejected because it crosses the hazard polygon. The ridge route is the safest of the packed candidates.",
        "Priority weights are on screen so a juror can recompute the rank.",
        "Health shows language model down and routing precomputed. That is a rehearsed state, not a failure we hide.",
    ]:
        pdf.bullet(line)
    pdf.h2("Do not say this")
    for line in [
        "We predict that this slope will fail.",
        "This is live IMD or CWC weather.",
        "We dispatch NDMA, SDRF, or 112.",
        "We send official SMS.",
        "These are live Google or OSRM driving directions.",
        "Unconfirmed users are missing persons.",
        "The app works for every city in India today.",
        "The photo is understood by computer vision.",
    ]:
        pdf.bullet(line)

    pdf.h2("Labels on the product")
    pdf.row("LIVE", "The SOS or check-in the citizen just sent in this session.")
    pdf.row("SIMULATED", "Demo-clock reports, rainfall polygon, blocked road, shelter availability, assign/dismiss.")
    pdf.row("FUSED", "The incident that groups member evidence.")
    pdf.row("RULE", "Zones, isolation, visibility grid, priority, and the sitrep sentence when no model key is set.")
    pdf.row("PRECOMPUTED", "The two or three candidate routes scored against the hazard. No live router is connected.")
    pdf.row("OPTIONAL LLM", "If a key is set, it may rephrase the sitrep. It never writes coordinates, roads, or ranks.")

    pdf.add_page()
    pdf.h1("2. Opening (about 40 seconds)")
    pdf.p(
        "During a landslide, responders do not lack messages. Four people say landslide, road blocked, vehicle trapped, "
        "and send a photo. A navigation app may still offer the fastest road through the debris. "
        "A dashboard may treat silence as missing persons. AASHRAY tries to reduce that confusion for one valley, "
        "and it shows the holes in the picture instead of inventing certainty."
    )
    pdf.p(
        "We will do three things. First, a citizen SOS from the demo hill pin, which becomes evidence, not a public pin of a victim. "
        "Second, the responder picture: one fused incident, a warning until it is corroborated, and a rejected unsafe route. "
        "Third, we advance a demo clock. At tick 7 the last road is blocked and Gahar hamlet is marked isolated. "
        "The language model is off on purpose."
    )

    pdf.h1("3. Before you walk up")
    pdf.bullet("Backend: from the backend folder, start uvicorn on 127.0.0.1 port 8000.")
    pdf.bullet("Frontend: from the frontend folder, start Vite on 127.0.0.1 port 5173.")
    pdf.bullet("Open http://127.0.0.1:5173. Zoom the browser so the disaster-alert banner and Send SOS are both visible.")
    pdf.bullet("Have a second window or a second login ready for the responder: ops@demo, password demo.")
    pdf.bullet("Citizen login is citizen@demo, password demo. Leave the pin on the demo hill (about 32.2395, 77.1880).")
    pdf.bullet("Optional check: http://127.0.0.1:8000/api/v1/health should show db ok, llm down, routing precomputed.")
    pdf.bullet("Do not tap Use my location unless you are physically in that valley. Your city's GPS will not grow a new road graph.")
    pdf.bullet("English / Hindi toggle is in the header. Switch once so the jury sees both, then stay in the language you will speak.")
    pdf.p(
        "If the database already has old demo ticks, say so: the clock is cumulative in this file. "
        "Isolation still means edge-14 is blocked. You can also explain that automated tests use a fresh database."
    )

    pdf.add_page()
    pdf.h1("4. The presentation, click by click")
    pdf.h2("Step A — Citizen, about one minute")
    pdf.bullet("Sign in as Citizen. Point at the logo and the bilingual toggle. Do not linger on the form.")
    pdf.bullet("Read the disaster-alert banner. Before any report it may say there is no alert yet. That is correct.")
    pdf.bullet("Press Send SOS. The green receipt must show an incident code such as A2719 and a cluster confidence percent.")
    pdf.bullet("Say: this percent is cluster confidence, not accuracy in the field.")
    pdf.bullet("The banner should become a Warning, not Critical. Say the next sentence immediately: one report is not allowed to raise Critical.")
    pdf.bullet("Point at the map: green line is the safer packed road, red dashed line is rejected because it crosses debris.")
    pdf.bullet("Optional: press I'm safe. That is a check-in for this registered demo user, not a census.")
    pdf.bullet("Optional photo: it is stored for the responder locker only. Say we do not run vision on it.")
    pdf.h2("Step B — Responder, about one minute")
    pdf.bullet("Log out. Sign in as Responder (ops@demo).")
    pdf.bullet("Header pills: Demo tick, Rainfall SIMULATED, Language model down, Routing PRECOMPUTED. Read them. Do not apologise.")
    pdf.bullet("Open the evidence locker for the incident. Show the SOS text, source live, and the confidence.")
    pdf.bullet("Priority card: score, weights, nearest resource, and the words that availability is simulated.")
    pdf.bullet("Assign team. Say this only writes a simulated status. It does not call a department.")
    pdf.h2("Step C — Demo clock, about one minute")
    pdf.bullet("Press Advance clock. Tick 1 sets simulated rainfall index to 1. The risk polygon is an estimation layer, not IMD.")
    pdf.bullet("Tick 2 injects four scripted reports through the same ingest path as a live SOS. They should fuse toward one incident if they match the hill.")
    pdf.bullet("Tick 5 is a town check-in, which changes visibility coverage. Unconfirmed is the count of seeded users who have not checked in.")
    pdf.bullet("Keep advancing to tick 7. The banner must name Gahar hamlet as isolated, with a medical-access delay as a one-hop rule, not a forecast.")
    pdf.bullet("Sitrep text is on the side. If it says Sitrep RULE, the model was not used. That is the honest default.")
    pdf.h2("Step D — Close, 20 seconds")
    pdf.p(
        "What we showed is fusion, corroboration, a safer-not-faster route, and an access cut, on one laptop, with the model down. "
        "What we did not show is national coverage, live weather, or a real dispatch. That is the boundary of this prototype."
    )

    pdf.add_page()
    pdf.h1("5. What each screen is allowed to prove")
    pdf.row("Disaster alert banner", "The citizen's saved location is inside a rule-based zone: Critical, Warning, or Nearby. Critical is withheld until corroboration.")
    pdf.row("SOS receipt", "The row was stored and linked to an incident code. It is evidence. Other citizens never see this exact text.")
    pdf.row("Map lines", "Precomputed polylines. Green is the remaining lowest-duration candidate that does not hit the hazard. Red is rejected, with a reason.")
    pdf.row("Shelters", "Names from the scenario pack. Availability is simulated.")
    pdf.row("SMS card", "A short text the user can copy if the network dies. Nothing is sent.")
    pdf.row("Ops layers", "Incidents, simulated risk, zones, visibility grid, routes, facilities, check-ins, blocked roads. Each layer has a source and a time.")
    pdf.row("Visibility percent", "Check-ins among simulated registered users in this demo, not a district population.")
    pdf.row("Isolation banner", "Graph result after edge-14 is blocked. Medical delay is the one-hop consequence we encoded, labelled as estimation.")

    pdf.h1("6. How the software actually works")
    pdf.p(
        "One FastAPI process and one SQLite file. The React app polls the snapshot about every two seconds. "
        "There is no message bus, no PostGIS, no Firebase, and no Kubernetes. That is a choice for a jury laptop, not a claim of national scale."
    )
    pdf.h2("From SOS to incident")
    pdf.p(
        "POST /api/v1/evidence writes the evidence row first, then fusion runs in the same process because the volume is tiny. "
        "The citizen gets a code immediately. Fusion score is 0.40 times geographic closeness, plus 0.25 times time closeness, "
        "plus 0.20 times category match, plus 0.15 times text similarity. Text similarity is TF-IDF on this small corpus, not a trained landslide model. "
        "If the best score is at least 0.65, the report joins an existing incident. Otherwise it starts a new one."
    )
    pdf.h2("Decisions that are rules, not a model")
    pdf.bullet("Zones: buffer the fused point and clip it to a valley mask so Critical is not a circle around a panic tap.")
    pdf.bullet("Corroboration: Critical only if there are at least two member reports, or an SOS while the rainfall index is at least 1.")
    pdf.bullet("Isolation: remove blocked edges from a small hill-road graph and search outward from the hub. If Gahar cannot be reached, it is isolated.")
    pdf.bullet("Routes: intersect each packed line with the hazard polygon. Reject hits. Among the rest, prefer the shorter duration. This is not a live router.")
    pdf.bullet("Priority: a visible weighted sum, with an isolation multiplier of 1.5. Nearest suitable facility is suggested. Availability is simulated.")
    pdf.bullet("Sitrep: a sentence built from those fields. A language model may replace the wording only if a key is configured. It is not allowed to invent a road or a coordinate.")
    pdf.h2("Who can see what")
    pdf.p(
        "Citizen login sees their own alert, their own check-in, the safer route, and shelters. "
        "They do not see other people's SOS text or photos. Responder login sees the locker. "
        "Photos, if uploaded, are served only with a responder token. Passwords in the demo are the word demo. That is a seeded classroom login, not production identity."
    )

    pdf.add_page()
    pdf.h1("7. Questions a national jury will ask")
    pdf.p("Answer in the first sentence. Then offer the screen. Do not add a feature you did not build.")

    pdf.h2("Product and problem")
    pdf.qa(
        "Isn't this just another SOS app?",
        "An SOS here is evidence. The operational object is the fused incident. Four nearby wordings can become one code, with a score you can argue with, and the fast road through debris is rejected.",
    )
    pdf.qa(
        "What problem are you actually solving?",
        "Responders already get messages. They do not get one picture of what is a single event, which road is unsafe, which hamlet lost its last road, and where safety status is simply unknown.",
    )
    pdf.qa(
        "Why only a landslide? India has floods and cyclones.",
        "One hazard, done so the jury can see fusion, zones, isolation, and routing. Multi-hazard national coverage is future work. We do not pretend this build is that system.",
    )
    pdf.qa(
        "Who is the user?",
        "Two roles in this prototype: a citizen who reports and checks in, and a simulated responder at a desk. There is no ministry portal, because we have no authority to operate one.",
    )
    pdf.qa(
        "What is the social outcome you can measure today?",
        "Time to a corroborated picture, and visibility coverage among the seeded users. We do not claim lives saved.",
    )

    pdf.h2("The demo they just watched")
    pdf.qa(
        "Why did my single SOS stay a Warning?",
        "By design. Critical needs corroboration: a second report, or this SOS plus the simulated rainfall index. One panic tap must not paint a critical zone.",
    )
    pdf.qa(
        "Why is there no alert at my house?",
        "The decision layers exist for one packed valley near Manali, about 32.24 north, 77.19 east. Use my location only moves the pin. It does not download a new road network for your city.",
    )
    pdf.qa(
        "Are these live maps?",
        "The pictures are real satellite and terrain tiles of that valley. The incident, the blocked edge, the shelters, and the routes are scenario files we authored. The tiles are not a disaster feed.",
    )
    pdf.qa(
        "Advance clock did nothing dramatic at tick 3.",
        "Only some ticks carry events. Tick 1 is rain, tick 2 is four reports, tick 5 is a check-in, tick 7 blocks edge-14. Empty ticks still move the clock. That is documented on the responder screen.",
    )
    pdf.qa(
        "The incident was already there when we opened the app.",
        "This demo database keeps earlier SOS rows. Say that, then either show the locker or advance the clock to isolation. Tests recreate the story on a clean database.",
    )

    pdf.h2("AI, and the model that is down")
    pdf.qa(
        "Where is the AI if the language model is down?",
        "The decisions do not use it. Fusion uses geography, time, category, and TF-IDF text similarity. Zones, isolation, routes, and priority are deterministic. The model is optional language on top of a sitrep we already computed.",
    )
    pdf.qa(
        "So you are predicting landslides?",
        "No. The rainfall and slope polygon is a simulated estimation layer for the story. We do not say this slope will fail. We do not train a landslide network.",
    )
    pdf.qa(
        "What does cluster confidence mean?",
        "It is the fusion score, shown as a percent. The screen says it is not field accuracy. A juror should treat 40 percent as weak agreement, not as a probability the hill has moved.",
    )
    pdf.qa(
        "Why not embeddings or a fine-tuned model?",
        "TF-IDF runs offline on a laptop with no key. Embeddings and a local large model are heavier and still would not be allowed to move roads or ranks. We kept the fallback we can defend when the hall Wi-Fi fails.",
    )
    pdf.qa(
        "Can the model hallucinate a village?",
        "Not in this design. If it is called, it only rewrites a short sitrep from JSON we already stored. Coordinates, blocked edges, and scores are written by code.",
    )
    pdf.qa(
        "You uploaded a photo. Did vision tag it?",
        "No. The file is stored and shown to the responder as evidence. There are no automatic debris tags. Saying otherwise would be false.",
    )

    pdf.add_page()
    pdf.h2("Maps, weather, and routes")
    pdf.qa(
        "Why not Google Maps?",
        "A Maps clone optimises travel time. Our claim is the opposite: reject the fast path that crosses the hazard. Google also needs a billed key. We score a few packed lines with geometry.",
    )
    pdf.qa(
        "Is routing live?",
        "No. Health says precomputed. Shapely tests whether each line hits the hazard or a blocked edge. If we later set an OSRM server, we would still need to label it live only when that call succeeds. Today it does not.",
    )
    pdf.qa(
        "Is the rain from IMD?",
        "No. Tick 1 writes a rainfall index in our database. The risk polygon is marked simulated. A real build would replace that index with a weather API for the same latitude and longitude. The corroboration rule would stay.",
    )
    pdf.qa(
        "How do you know the hamlet is cut off? It might just be far from the pin.",
        "Distance is the wrong test. We remove edge-14 from a small graph of this valley and search from the hub. Gahar becomes unreachable. That is access-cut, and it multiplies priority.",
    )
    pdf.qa(
        "Is the medical delay real?",
        "It is a one-hop rule we wrote: last road blocked, so medical access may be delayed. It is an estimation on the banner, not an ambulance ETA from a live dispatch system.",
    )
    pdf.qa(
        "Are hospitals really open?",
        "We do not know. The card says availability is simulated. The rank is type match, then distance, inside the scenario pack.",
    )

    pdf.h2("SOS: who receives it?")
    pdf.qa(
        "When I press Send SOS, who gets it?",
        "This laptop. The API stores the evidence, fusion attaches an incident code, and the responder account sees it on the operations screen within a couple of seconds. No SMS gateway, no 112, no district control room is connected.",
    )
    pdf.qa(
        "Then how would a real desk receive it?",
        "The same pipeline: evidence, then a fused incident, then an authenticated responder view. Production would add real logins, a sound or push when a new incident appears, and, if the phone has no data, a telecom SMS gateway that drops the short text into that same inbox. A human still assigns a team. The app does not dispatch NDMA.",
    )
    pdf.qa(
        "What does Assign team do?",
        "It sets the incident status to assigned in SQLite. Dismiss sets dismissed. Both are simulated workflow buttons so the jury can see a desk action. They do not notify an agency.",
    )
    pdf.qa(
        "What if the network dies in the valley?",
        "The citizen screen shows a short SMS-shaped text and a copy button. We do not send it. There is no offline queue that retries later, and there is no mesh radio. We will not claim those.",
    )
    pdf.qa(
        "Can another citizen see my SOS or my photo?",
        "No. The citizen snapshot returns their own ids, their zone, and shared zone geometry. The locker is responder-only. That split is in the API, not only in the layout.",
    )

    pdf.h2("People, ethics, and false reports")
    pdf.qa(
        "Unconfirmed safety status — are those people missing?",
        "No. It is the number of simulated registered users in this demo who have not checked in. The copy on screen says it is not a missing-person count. Treating silence as missing would be an ethical error.",
    )
    pdf.qa(
        "What about a hoax?",
        "A responder can dismiss the incident. Critical also waits for corroboration, so one dramatic SOS does not become the highest alert by itself. We do not claim we detect hoaxes with AI.",
    )
    pdf.qa(
        "What if two reports disagree?",
        "The incident can carry a disagreement flag instead of silently averaging categories. If it is set, the locker line says so. We do not hide conflict.",
    )
    pdf.qa(
        "Is collecting location and photos safe?",
        "For this prototype, data stays in a local SQLite file and a local media folder. Photos are not on the public map. A production system would need consent, retention, and access logs we have not built. We should say that limit out loud.",
    )

    pdf.add_page()
    pdf.h2("Engineering and credibility")
    pdf.qa(
        "Why SQLite and one process? That will not scale to a state.",
        "Correct. It is the right shape for a three-minute demo that must boot on jury Wi-Fi. Scale would mean a larger database and more than one worker. We do not claim we load-tested a state.",
    )
    pdf.qa(
        "How do we know this is not a slide?",
        "Backend tests cover fusion of four reports into one incident, the corroboration gate, route rejection, and isolation at tick 7. A browser test signs in, sends SOS, advances seven ticks, sees Gahar isolated, and assigns the incident. The model is off in those tests.",
    )
    pdf.qa(
        "What is the fusion formula so I can recompute it?",
        "0.40 geography, 0.25 time, 0.20 category, 0.15 text. Attach at 0.65 or above. Priority weights are also drawn on the responder chart: severity, people, critical check-ins, hours, kilometres, and an isolation multiplier.",
    )
    pdf.qa(
        "What did you deliberately not build?",
        "Live IMD, official SMS, OSRM calls, computer vision, household check-in, a national multi-hazard model, mesh networking, Kafka, PostGIS, and Kubernetes.",
    )
    pdf.qa(
        "The README used to sound like a national multi-hazard platform.",
        "That sentence was wrong for this repository. The README now matches the prototype: one landslide scenario, labelled layers, and no official dispatch.",
    )

    pdf.h2("Road from this prototype to a real deployment")
    pdf.p("Say this as a plan, not as a feature you have finished.")
    pdf.bullet("Location: keep GPS on the phone, and load OpenStreetMap roads and facilities for that bounding box instead of one hand-packed valley.")
    pdf.bullet("Weather: replace the demo rainfall index with a scheduled read from a weather service for that coordinate. Keep the same corroboration rule.")
    pdf.bullet("Receive path: real responder accounts, a notification when a fused incident appears, and an SMS gateway only as the no-data fallback into the same evidence table.")
    pdf.bullet("Authority: no dispatch until an actual agency agreement exists. Until then, assign remains a status inside our system.")
    pdf.p(
        "The part we would not throw away is the split between evidence and incident, the corroboration gate, the access-cut test, and the refusal to rank silence as missing."
    )

    pdf.add_page()
    pdf.h1("8. If something breaks on stage")
    pdf.row("Page will not load", "API or Vite is down. Say the health URL. Do not invent data. Offer the test list: 24 backend tests and the browser golden path, if you have that window.")
    pdf.row("SOS button errors", "The red line means the API on port 8000 did not accept the call. Check that uvicorn is running. Do not resend ten times.")
    pdf.row("Alert stays empty", "The saved citizen location is outside the valley zones. Use the demo hill pin and send SOS again. Do not switch on personal GPS in another city.")
    pdf.row("No Critical banner", "That can be correct. Explain corroboration. Advance the clock to tick 1 or show a second report.")
    pdf.row("No Gahar banner", "You have not reached tick 7, or edge-14 was not applied. Keep pressing Advance clock until the tick pill shows 7.")
    pdf.row("Map tiles are blank", "The hall blocked the tile server. The vectors (zones and routes) are still ours. Say the basemap is a third-party tile, and the decision geometry is local.")
    pdf.row("Judge asks for their city", "Repeat the boundary. We can place a pin. We cannot invent a road graph we did not pack.")

    pdf.h1("9. Accounts, ticks, and files")
    pdf.row("Citizen", "citizen@demo  /  demo")
    pdf.row("Responder", "ops@demo  /  demo")
    pdf.row("Other seeded citizens", "hamlet.a@demo, hamlet.b@demo, town.b@demo, same password.")
    pdf.row("App", "http://127.0.0.1:5173")
    pdf.row("API docs", "http://127.0.0.1:8000/docs")
    pdf.row("Tick 1", "Simulated rainfall index = 1.")
    pdf.row("Tick 2", "Four scripted reports on the hill.")
    pdf.row("Tick 5", "Town check-in for visibility.")
    pdf.row("Tick 7", "Block edge-14. Gahar hamlet isolated.")
    pdf.row("Scenario files", "backend/aashray/scenario : graph, valley mask, settlements, ticks, routes.")
    pdf.row("Claims note", "docs/CLAIMS.md")
    pdf.row("Architecture note", "docs/ARCHITECTURE.md")

    pdf.h1("10. Last line, then stop")
    pdf.p(
        "AASHRAY reduces confusion in the first hour of one landslide story: many reports become one incident, "
        "the unsafe fast road is rejected, the cut-off hamlet is a graph fact, and the people we have not heard from "
        "stay marked unconfirmed rather than missing. The model can be unplugged. The government is not plugged in. "
        "Both of those sentences are part of the demonstration."
    )

    pdf.output(str(OUT))
    print(OUT, OUT.stat().st_size)


if __name__ == "__main__":
    build()
