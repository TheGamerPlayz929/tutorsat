from .base import build_choices

WIC_FRAMES = {
    "easy": [
        {"text": "Because the trail had dried out overnight, the hikers set off at a "
                 "______ pace.",
         "answer": "brisk",
         "distractors": ["sluggish", "wary", "treacherous"],
         "explanation": "A dried trail removes the obstacle that would force a slow or "
                        "careful pace, so 'brisk' fits the causal cue 'because'."},
        {"text": "The recipe is ______: it lists only five ingredients and takes ten "
                 "minutes.",
         "answer": "simple",
         "distractors": ["elaborate", "costly", "secretive"],
         "explanation": "Few ingredients and little time support 'simple'; the colon "
                        "signals the clause explains the blank."},
        {"text": "After the storm knocked out the power, the town issued a ______ "
                 "asking residents to conserve water.",
         "answer": "notice",
         "distractors": ["penalty", "forecast", "recipe"],
         "explanation": "An official request to conserve water is a notice; the other "
                        "nouns do not fit 'issued a ___ asking residents to...'."},
        {"text": "To keep the soup from sticking to the pot, stir it ______.",
         "answer": "occasionally",
         "distractors": ["permanently", "reluctantly", "formally"],
         "explanation": "Preventing sticking requires periodic stirring; the purpose "
                        "clause rules out the other adverbs."},
        {"text": "The garden path was completely ______ after weeks of rain, so "
                 "visitors were told to wear boots.",
         "answer": "muddy",
         "distractors": ["swept", "paved", "arid"],
         "explanation": "Weeks of rain produce mud, and boots suit a muddy path; "
                        "'so' links the weather to the condition."},
        {"text": "Because the ferry runs only twice a day, missing it means a long "
                 "______.",
         "answer": "delay",
         "distractors": ["voyage", "discount", "reservation"],
         "explanation": "Missing the boat forces waiting until the next sailing: a "
                        "delay. The causal 'because' points at the consequence."},
        {"text": "The lecture was so ______ that several students quietly slipped "
                 "out halfway through.",
         "answer": "tedious",
         "distractors": ["riveting", "brief", "optional"],
         "explanation": "Slipping out signals boredom; 'so ... that' makes the blank "
                        "the cause of the exits."},
        {"text": "To shield the seedlings from frost, the farmer spread an ______ "
                 "layer of straw over the beds.",
         "answer": "insulating",
         "distractors": ["ornamental", "edible", "optional"],
         "explanation": "Protecting from frost requires insulation; the purpose "
                        "phrase 'to shield' selects it."},
    ],
    "medium": [
        {"text": "Critics dismissed the novel as sentimental, yet its ______ portrayal "
                 "of grief moved many readers to tears.",
         "answer": "unsparing",
         "distractors": ["tender", "nostalgic", "idealized"],
         "explanation": "'Yet' signals contrast with 'sentimental'; an unsparing "
                        "(unflinching) portrayal contrasts with sentimental treatment."},
        {"text": "The committee's report was deliberately ______, avoiding technical "
                 "terms so that any resident could understand it.",
         "answer": "accessible",
         "distractors": ["exclusive", "terse", "confidential"],
         "explanation": "Avoiding jargon so anyone can understand defines accessible "
                        "writing; 'terse' concerns brevity, not clarity."},
        {"text": "Rather than ______ the problem, the mayor confronted it directly in "
                 "her opening remarks.",
         "answer": "evading",
         "distractors": ["celebrating", "documenting", "exaggerating"],
         "explanation": "'Rather than' sets up a contrast with confronting directly, "
                        "which is the opposite of evading."},
        {"text": "Although the early data seemed to ______ the team's hypothesis, "
                 "further trials revealed a measurement error, and support for the "
                 "hypothesis returned.",
         "answer": "undermine",
         "distractors": ["confirm", "require", "summarize"],
         "explanation": "Support 'returned' after the error was found, so the flawed "
                        "data must have appeared to weaken ('undermine') the hypothesis."},
        {"text": "The manuscript was remarkable not for what it included but for what "
                 "it quietly ______: any mention of the dispute was absent.",
         "answer": "omitted",
         "distractors": ["celebrated", "summarized", "predicted"],
         "explanation": "'Absent' and the contrast with 'included' require omitting; "
                        "the colon introduces the evidence for the blank."},
        {"text": "Her reading of the contract rests on a ______ chain of inference, "
                 "each link weaker than the one before it.",
         "answer": "fragile",
         "distractors": ["rigorous", "direct", "published"],
         "explanation": "'Each link weaker' describes a fragile chain; the appositive "
                        "phrase defines the blank."},
        {"text": "The old bridge was closed to cars but stayed open to foot traffic, "
                 "a compromise that ______ both preservation and practical needs.",
         "answer": "balanced",
         "distractors": ["abandoned", "ignored", "complicated"],
         "explanation": "A partial closure serving two kinds of needs is best "
                        "described as balancing them."},
        {"text": "Long treated as a mere stopover, the port town has since been "
                 "______ among the region's essential destinations.",
         "answer": "ranked",
         "distractors": ["lost", "charged", "refunded"],
         "explanation": "'Among the essential destinations' calls for ranked; the "
                        "contrast with 'mere stopover' marks the change in standing."},
    ],
    "hard": [
        {"text": "Far from being ______, the settlement's earliest laws reveal a "
                 "striking attention to individual property rights.",
         "answer": "haphazard",
         "distractors": ["orderly", "authoritarian", "obsolete"],
         "explanation": "'Far from being X, ... reveal striking attention to order' "
                        "requires X to mean lacking order: haphazard."},
        {"text": "The pianist's interpretation was anything but reverent: her ______ "
                 "tempo changes startled an audience expecting deference to the score.",
         "answer": "audacious",
         "distractors": ["meticulous", "measured", "orthodox"],
         "explanation": "Anything but reverent, startling those expecting deference, "
                        "calls for audacious (bold) tempo changes."},
        {"text": "Biologists once assumed the species bred only in spring, but recent "
                 "fieldwork suggests its breeding schedule is more ______ than "
                 "previously thought.",
         "answer": "flexible",
         "distractors": ["seasonal", "predictable", "ritualized"],
         "explanation": "Evidence against a fixed spring pattern implies the schedule "
                        "is more flexible than assumed."},
        {"text": "The archivist's catalog was so ______ that even veteran researchers "
                 "needed a guide to navigate it.",
         "answer": "convoluted",
         "distractors": ["intuitive", "concise", "annotated"],
         "explanation": "Needing a guide to navigate signals excessive complexity: "
                        "convoluted. The 'so...that' structure links cause and effect."},
        {"text": "The biography resists the genre's usual arc: rather than tracing a "
                 "steady rise, it charts a career punctuated by ______ reversals.",
         "answer": "abrupt",
         "distractors": ["inevitable", "gradual", "deserved"],
         "explanation": "'Rather than a steady rise' requires reversals that break "
                        "steadiness: abrupt ones."},
        {"text": "Far from ______ the controversy, the committee's cautious wording "
                 "only sharpened it.",
         "answer": "defusing",
         "distractors": ["igniting", "studying", "recording"],
         "explanation": "'Only sharpened' contrasts with the blank via 'far from': "
                        "the wording failed to defuse the dispute."},
        {"text": "What the novel loses in plot it recovers in texture: its ______ "
                 "attention to ordinary labor elevates scenes of housework and harvest.",
         "answer": "minute",
         "distractors": ["casual", "hasty", "fictional"],
         "explanation": "'Recovers in texture' implies fine-grained closeness; minute "
                        "(pronounced my-NEWT) means extremely detailed."},
        {"text": "The archive's value lies less in individual documents than in their "
                 "______: read together, the letters map a decade of quiet dissent.",
         "answer": "accumulation",
         "distractors": ["destruction", "isolation", "appraisal"],
         "explanation": "'Read together' and 'less than individual' point to the "
                        "power of accumulation; isolation states the opposite."},
    ],
}

PURPOSE_PASSAGES = [
    {"tier": "easy",
     "passage": ("Some researchers argue that walking meetings improve workplace "
                 "creativity. In one study, employees who walked during group "
                 "meetings produced about twice as many novel ideas as seated groups "
                 "did. Critics note that energetic employees may simply choose to "
                 "walk more. Even so, several companies now schedule short walks "
                 "before brainstorming sessions."),
     "correct": ("Present a claim about walking meetings and cite supporting "
                 "evidence while acknowledging a limitation"),
     "distractors": ["Narrate the history of one company's meetings chronologically",
                     "Argue that research on workplace creativity should be abandoned",
                     "Compare two competing models of office furniture"]},
    {"tier": "easy",
     "passage": ("The town of Bell Harbor paints its fire hydrants in bright designs "
                 "chosen by local artists. The project began when a retired painter "
                 "suggested it to the city council. Each design must still meet "
                 "visibility rules set by the fire department, and hydrants are "
                 "repainted whenever the paint fades below those standards."),
     "correct": ("Describe a public art project and explain how it balances "
                 "creativity with safety requirements"),
     "distractors": ["Persuade readers that all hydrants should be painted by artists",
                     "Explain why fire departments oppose public art projects",
                     "Recount a single artist's career from beginning to end"]},
    {"tier": "medium",
     "passage": ("For decades, the Meadowbrook covered bridge carried farm trucks "
                 "across the Otter River. When a new concrete span opened nearby, the "
                 "old bridge was scheduled for demolition. Residents formed a "
                 "preservation society and raised money to restore the structure as a "
                 "pedestrian walkway. The bridge now anchors an annual river festival "
                 "that draws visitors from across the county."),
     "correct": ("Trace how a threatened structure gained a new civic role through "
                 "community action"),
     "distractors": ["Argue that covered bridges are safer than concrete spans",
                     "Describe the engineering methods used to restore the bridge",
                     "Criticize county officials for wasting money on festivals"]},
    {"tier": "medium",
     "passage": ("Sociologist Dana Whitfield spent two years observing a community "
                 "kitchen where volunteers prepare meals from surplus grocery-store "
                 "produce. She found that most volunteers return not because of the "
                 "meals themselves but because the kitchen gives them a regular place "
                 "to know their neighbors. Whitfield argues that such kitchens work "
                 "best when organizers protect time for conversation instead of "
                 "maximizing efficiency."),
     "correct": ("Summarize research findings about why volunteers value community "
                 "kitchens"),
     "distractors": ["Recruit new volunteers for a community kitchen program",
                     "Prove that surplus produce could eliminate hunger entirely",
                     "Compare Whitfield's career with those of earlier sociologists"]},
    {"tier": "hard",
     "passage": ("Early critics dismissed the paintings of Alma Reyes because she had "
                 "no formal training; her canvases used house paint and salvaged wood "
                 "for frames. Yet the very directness that troubled those critics "
                 "became central to her reputation: later scholars argued that "
                 "Reyes's materials recorded, with unusual honesty, the economic "
                 "limits of the neighborhood she depicted."),
     "correct": ("Explain how qualities that once drew criticism came to define an "
                 "artist's standing"),
     "distractors": ["Claim that formal training is unnecessary for artistic success",
                     "Catalog every material Reyes used across her career",
                     "Contrast Reyes's neighborhood with wealthier districts at length"]},
    {"tier": "easy",
     "passage": ("The county's seed library lends heirloom seeds the way branches "
                 "lend books. Borrowers return nothing in spring; instead they save "
                 "seeds from whatever grew best and bring those back in autumn. The "
                 "exchange keeps local plant strains adapting to local soil."),
     "correct": ("Explain how a seed library operates and why its design suits its "
                 "purpose"),
     "distractors": ["Persuade farmers to abandon commercial seed companies",
                     "Rank several competing seed-lending programs by size",
                     "Follow one gardener through a single season day by day"]},
    {"tier": "medium",
     "passage": ("When the state capped annual rent increases, landlords warned that "
                 "building maintenance would suffer. Economists tracking the policy "
                 "found instead that repair requests rose slightly, though they note "
                 "that some owners shifted units toward short-term rentals, "
                 "shrinking the long-term housing supply."),
     "correct": ("Report early evidence that complicates both sides' predictions "
                 "about a rent cap"),
     "distractors": ["Argue that the rent cap should be repealed immediately",
                     "Explain how economists measure repair requests",
                     "Contrast rent policies across several different states"]},
    {"tier": "hard",
     "passage": ("Linguists documenting Alarne, a language spoken fluently by fewer "
                 "than two hundred people, expected its grammar to simplify as usage "
                 "faded. Instead, younger speakers have invented honorific forms no "
                 "elder uses. The finding unsettles a tidy assumption: contraction "
                 "does not always mean simplification."),
     "correct": ("Present research findings that overturn an expectation about how "
                 "languages change"),
     "distractors": ["Advocate for teaching Alarne in regional schools",
                     "Define honorific speech for a general audience",
                     "Recount the linguists' fieldwork trip chronologically"]},
    {"tier": "hard",
     "passage": ("The museum's conservators chose visible repair for the shattered "
                 "vase, filling its cracks with gold-toned lacquer rather than "
                 "disguising them. The choice reads as argument as much as "
                 "technique: the display proposes that damage, honestly marked, "
                 "belongs to an object's history."),
     "correct": ("Interpret a conservation choice as making a claim about damage "
                 "and history"),
     "distractors": ["Describe the chemical properties of gold-toned lacquer",
                     "Chronicle the vase's owners from creation to display",
                     "Criticize museums for failing to restore objects invisibly"]},
]

CTC_ENTRIES = [
    {"tier": "easy",
     "text1": "Adding protected bike lanes downtown will reduce traffic injuries.",
     "stances": {
         "supports": "Cities that installed protected lanes saw injury rates fall "
                     "within two years.",
         "contradicts": "Injury rates on our city's Main Street rose after protected "
                        "lanes were installed there.",
         "complicates": "Protected lanes reduced car-bike collisions on some streets "
                        "but increased them at intersections."}},
    {"tier": "easy",
     "text1": "Later school start times improve student alertness.",
     "stances": {
         "supports": "Students at schools that delayed start times reported feeling "
                     "less sleepy during morning classes.",
         "contradicts": "A large survey found no change in student alertness after "
                        "start times shifted later.",
         "complicates": "Alertness improved for older teens but declined for students "
                        "with long bus commutes."}},
    {"tier": "medium",
     "text1": "Common houseplants meaningfully improve indoor air quality.",
     "stances": {
         "supports": "Chamber studies show several common houseplants absorb certain "
                     "airborne compounds.",
         "contradicts": "Building-scale tests find plants remove far too little of "
                        "these compounds to matter.",
         "complicates": "Houseplants filter some chemicals effectively while doing "
                        "almost nothing for others."}},
    {"tier": "medium",
     "text1": "Four-day workweeks raise employee productivity.",
     "stances": {
         "supports": "Trial firms produced the same output in four days as they had "
                     "in five.",
         "contradicts": "Weekly output fell at firms that cut to four days without "
                        "reducing total workload.",
         "complicates": "Productivity rose for office roles but did not improve in "
                        "shift-based roles."}},
    {"tier": "easy",
     "text1": "School gardens increase children's vegetable intake.",
     "stances": {
         "supports": "Students at schools with gardens reported eating more "
                     "vegetables each week.",
         "contradicts": "Intake surveys showed no difference between garden and "
                        "non-garden schools.",
         "complicates": "Garden students ate more vegetables at school but not at "
                        "home."}},
    {"tier": "medium",
     "text1": "Cities should convert vacant lots into pocket parks.",
     "stances": {
         "supports": "Neighborhoods that added pocket parks reported rising "
                     "resident satisfaction.",
         "contradicts": "Several converted lots fell into disrepair because upkeep "
                        "lapsed after opening.",
         "complicates": "Pocket parks lifted satisfaction on quiet streets while "
                        "drawing noise complaints on busy ones."}},
    {"tier": "hard",
     "text1": "Automated essay scoring is reliable enough for college placement "
              "decisions.",
     "stances": {
         "supports": "On double-scored samples, machine-human agreement matches "
                     "human-human agreement.",
         "contradicts": "Adversarial essays padded with sophisticated gibberish "
                        "earned passing machine scores.",
         "complicates": "The software agrees with human readers on structure but "
                        "penalizes unconventional yet valid arguments."}},
    {"tier": "hard",
     "text1": "Four-day school weeks harm student achievement.",
     "stances": {
         "supports": "Test scores dipped in districts after the switch to four days.",
         "contradicts": "Districts on four-day weeks matched five-day districts' "
                        "scores.",
         "complicates": "Scores held steady overall but fell for students without "
                        "reliable home internet."}},
]

MAIN_IDEA_ITEMS = [
    {"tier": "easy",
     "passage": ("Maplewood's public library has started a tool-lending program. "
                 "Residents can borrow drills, saws, and sewing machines the way they "
                 "borrow books. The program is funded by a small city grant and run "
                 "by two librarians. In its first year, more than four hundred "
                 "households borrowed at least one tool."),
     "correct": "Maplewood's library lends tools to residents, and many households use the service.",
     "too_narrow": "More than four hundred households borrowed tools in the first year.",
     "not_stated": "Tool-lending programs are common throughout the region.",
     "contradicts": "The library's tool program is funded by the state government."},
    {"tier": "easy",
     "passage": ("A retired mail carrier in Cedar Falls turned his old route notes "
                 "into a small book about the neighborhood's dogs. Each entry names "
                 "the dog, describes its bark, and records where it likes to nap. "
                 "The self-published booklet sold out its first printing at the "
                 "hardware store."),
     "correct": "A carrier's detailed route observations became a popular little book.",
     "too_narrow": "The booklet's first printing sold out at a hardware store.",
     "not_stated": "Cedar Falls requires all dogs to be registered.",
     "contradicts": "The carrier discarded his route notes upon retiring."},
    {"tier": "medium",
     "passage": ("The village clock has run four minutes slow since 1971, and "
                 "residents prefer it that way. Twice, repair offers promised exact "
                 "timekeeping; twice, petitions preserved the drift. Its keeper says "
                 "the lag grants everyone a small grace period they can rely on."),
     "correct": "A flawed town clock survives because residents treasure its familiar imperfection.",
     "too_narrow": "The village clock has been four minutes slow since 1971.",
     "not_stated": "The clockkeeper is appointed by the mayor.",
     "contradicts": "Repairs corrected the clock's drift in the 1990s."},
    {"tier": "medium",
     "passage": ("When a new concrete span opened near the old Meadowbrook bridge, "
                 "the covered bridge was slated for demolition. Residents organized, "
                 "raised restoration funds, and reopened it as a pedestrian walkway. "
                 "It now anchors an annual river festival."),
     "correct": "Community organizing gave a condemned bridge a second life as a public space.",
     "too_narrow": "Residents raised money to restore the Meadowbrook bridge.",
     "not_stated": "Covered bridges attract more tourists than modern bridges.",
     "contradicts": "County officials demolished the bridge soon after the new span opened."},
    {"tier": "hard",
     "passage": ("Historians once credited crop rotation alone for the region's "
                 "medieval soil recovery. Recent pollen analysis suggests a second "
                 "factor: as wetlands were drained, nitrogen-rich sediments spread "
                 "onto fields during floods. The revision does not diminish "
                 "rotation's role; it widens the cast of causes."),
     "correct": "New evidence points to overlapping causes behind a known agricultural recovery.",
     "too_narrow": "Pollen analysis identified nitrogen-rich sediments on flood-exposed fields.",
     "not_stated": "Wetland drainage began centuries before crop rotation.",
     "contradicts": "Crop rotation contributed nothing to the soil recovery."},
    {"tier": "hard",
     "passage": ("For decades, scholars debated whether the astronomer's late "
                 "notebooks showed hesitation or confidence about her comet's "
                 "orbit. The notebooks themselves burned in a 1911 archive fire, "
                 "and the debate ran on memory alone. A recently cataloged "
                 "observatory ledger, her assistant's daily log, now records her "
                 "recalculating the orbit nightly for six weeks before announcing "
                 "it, settling the question toward deliberate caution."),
     "correct": "A newly found record resolves an old debate about an astronomer's certainty.",
     "too_narrow": "The ledger records six weeks of nightly recalculation before the announcement.",
     "not_stated": "The 1911 fire destroyed most of the city's archives.",
     "contradicts": "The notebooks survive intact in a private collection."},
]

CLAIM_EVIDENCE_TOPICS = [
    {"tier": "easy",
     "claim": "Students who eat breakfast before school perform better on morning tests.",
     "support": lambda n, hi, lo: (
         f"In a study of {n} schools, students who ate breakfast averaged {hi}% on "
         f"morning tests compared with {lo}% among students who skipped breakfast."),
     "wrong_kinds": [
         lambda n, hi, lo: f"Students reported that breakfast foods taste better than vending-machine snacks.",
         lambda n, hi, lo: f"Afternoon test scores were nearly identical across breakfast habits.",
         lambda n, hi, lo: f"Breakfast programs cost schools about two dollars per student per week."]},
    {"tier": "medium",
     "claim": "Office workers focus better when plants are visible at their desks.",
     "support": lambda n, hi, lo: (
         f"Across {n} offices, workers with desk plants completed a proofreading task "
         f"{hi - lo}% faster than workers without them."),
     "wrong_kinds": [
         lambda n, hi, lo: f"Most workers said they prefer plants to posters when decorating.",
         lambda n, hi, lo: f"Plants reduced measured noise levels slightly in open offices.",
         lambda n, hi, lo: f"The most common desk plants cost under ten dollars each."]},
    {"tier": "medium",
     "claim": "Neighborhood watch signs reduce daytime break-ins.",
     "support": lambda n, hi, lo: (
         f"Blocks displaying {n} new signs saw reported daytime break-ins fall to "
         f"{lo} per year, down from {hi}, while sign-free blocks stayed flat."),
     "wrong_kinds": [
         lambda n, hi, lo: f"Residents on signed blocks said they feel safer walking at night.",
         lambda n, hi, lo: f"The average sign costs about forty dollars to produce and install.",
         lambda n, hi, lo: f"Nighttime break-ins fell across the whole city during the study."]},
    {"tier": "hard",
     "claim": "Extending sleep improves free-throw accuracy in young basketball players.",
     "support": lambda n, hi, lo: (
         f"Players who extended sleep for {n} nights made {hi}% of free throws in "
         f"post-tests, up from a {lo}% baseline measured beforehand."),
     "wrong_kinds": [
         lambda n, hi, lo: f"Players reported enjoying later wake times during the extension period.",
         lambda n, hi, lo: f"Taller players tended to have higher shooting percentages overall.",
         lambda n, hi, lo: f"Practice minutes per week were similar across all players studied."]},
    {"tier": "hard",
     "claim": "Bilingual labels make product warnings easier to remember.",
     "support": lambda n, hi, lo: (
         f"After {n} minutes with bilingual warning labels, participants recalled "
         f"{hi}% of key hazards, versus {lo}% for single-language labels."),
     "wrong_kinds": [
         lambda n, hi, lo: f"Participants rated the bilingual labels as more attractive overall.",
         lambda n, hi, lo: f"Print shops charge slightly more for two-language packaging.",
         lambda n, hi, lo: f"Hazard symbols alone produced the fastest recognition times."]},
]

INFERENCE_ITEMS = [
    {"tier": "easy",
     "passage": ("The gallery displays paintings only from Tuesday through Saturday. "
                 "Admission is free on Wednesdays."),
     "correct": "A visitor who wants free admission should go on a Wednesday.",
     "wrongs": ["The gallery is open every day of the week.",
                "Admission is always free at the gallery.",
                "The gallery displays sculptures as well as paintings."]},
    {"tier": "easy",
     "passage": ("The plant nursery refunds any tree that fails to leaf out by "
                 "June 1. The nursery closes every Sunday."),
     "correct": "A customer cannot buy a refund-eligible tree there on a Sunday.",
     "wrongs": ["The nursery sells only trees.",
                "Refunds require a written request.",
                "The nursery opens late on Sundays."]},
    {"tier": "easy",
     "passage": ("The bakery sells rye bread only on Fridays and Saturdays. On "
                 "Saturdays, the bakery closes at noon."),
     "correct": "On some days the bakery sells rye bread before noon.",
     "wrongs": ["Rye bread sells out before noon on Fridays.",
                "The bakery closes at noon on both Friday and Saturday.",
                "The bakery sells rye bread on Sundays."]},
    {"tier": "medium",
     "passage": ("Every locker in Row C opens with a key, not a code. Over winter "
                 "break, exactly half of the Row C keys were replaced."),
     "correct": "At least some lockers in Row C use keys made before winter break.",
     "wrongs": ["No locker in Row C opens with a key.",
                "Every key for Row C was replaced over winter break.",
                "Some lockers in Row C open with codes."]},
    {"tier": "medium",
     "passage": ("The shuttle runs between the two campuses every twenty minutes. "
                 "The first shuttle leaves the north campus at 7:10 a.m."),
     "correct": "A shuttle departs the north campus at 7:30 a.m.",
     "wrongs": ["Shuttles leave both campuses at 7:10 a.m.",
                "The shuttle runs every twelve minutes.",
                "The last shuttle leaves after midnight."]},
    {"tier": "medium",
     "passage": ("Members who join after March pay a reduced initiation fee, but "
                 "every member pays the same annual dues each January."),
     "correct": "Two members who joined in different years pay the same January dues.",
     "wrongs": ["Members who joined earliest pay lower annual dues.",
                "The initiation fee is refunded every January.",
                "No member pays an initiation fee."]},
    {"tier": "hard",
     "passage": ("Every novel on the shelf is either historical fiction or a mystery. "
                 "All the mysteries were published after 1990, but some historical "
                 "fiction dates from earlier decades."),
     "correct": "Any book on the shelf published before 1990 is historical fiction.",
     "wrongs": ["Some mysteries on the shelf were published before 1990.",
                "Every historical novel on the shelf was published after 1990.",
                "No book on the shelf combines history and mystery elements."]},
    {"tier": "hard",
     "passage": ("Of the five speakers scheduled, three discuss geology and no two "
                 "talks overlap. The two non-geology talks run back to back."),
     "correct": "The schedule includes a stretch of at least two consecutive talks with no geology speaker.",
     "wrongs": ["No two geology talks ever run consecutively.",
                "Exactly two speakers discuss geology.",
                "All five talks overlap at some point."]},
]

BOUNDARY_CLAUSES = [
    ("The bakery opens at dawn", "its ovens glow before sunrise"),
    ("The ferry leaves every hour", "the dock fills up quickly"),
    ("Rain flooded the lower field", "the festival moved to the gymnasium"),
    ("The clock tower chimes at noon", "shopkeepers set their watches by it"),
    ("Volunteers repainted the community center", "neighbors donated most of the supplies"),
    ("The trail switchbacks up the ridge", "hikers gain a thousand feet by lunchtime"),
    ("The observatory opens to the public on Fridays", "volunteers staff the telescopes"),
    ("Snow closed the mountain pass", "mail trucks took the valley route"),
    ("The choir rehearses in the library basement", "the acoustics surprise first-time visitors"),
    ("Bees pollinate the orchard each May", "the harvest follows within the month"),
    ("The night market closes at midnight", "vendors begin packing an hour earlier"),
    ("A cold snap cracked the fountain", "the parks crew covered it through winter"),
]

INFINITIVE_VERBS = [
    ("extend", "extending", "extended", "extends"),
    ("review", "reviewing", "reviewed", "reviews"),
    ("postpone", "postponing", "postponed", "postpones"),
    ("revise", "revising", "revised", "revises"),
    ("renegotiate", "renegotiating", "renegotiated", "renegotiates"),
    ("survey", "surveying", "surveyed", "surveys"),
    ("restore", "restoring", "restored", "restores"),
    ("draft", "drafting", "drafted", "drafts"),
]
AGREEMENT_SUBJECTS = [
    "the planning board",
    "the school's principals",
    "each department head",
    "the tournament organizers",
    "the harbor committee",
    "every regional manager",
    "the museum's trustees",
    "both co-chairs",
]

RELATION_CONNECTORS = {
    "consequence": ["consequently", "therefore", "as a result"],
    "contrast": ["however", "nevertheless", "by contrast"],
    "addition": ["moreover", "furthermore", "likewise"],
}
TRANSITION_SETS = [
    ("consequence", "The soil in the valley is thin and nutrient-poor",
     "farmers there have long relied on imported fertilizer"),
    ("contrast", "Winter tourism keeps the town busy through February",
     "the months of March and April remain quiet"),
    ("addition", "The new library offers free tutoring on weekdays",
     "it hosts weekend coding clubs for teenagers"),
    ("consequence", "The bridge closed for repairs",
     "commuters faced long detours for six weeks"),
    ("contrast", "The novel was panned by critics on release",
     "it found a devoted readership within a decade"),
    ("addition", "The clinic accepts walk-in patients",
     "it offers evening hours twice a week"),
    ("consequence", "Demand for the course doubled this year",
     "the department hired a second instructor"),
    ("contrast", "The recipe calls for few ingredients",
     "each step demands careful timing"),
    ("consequence", "The reservoir dropped below half capacity",
     "the city banned lawn watering through September"),
    ("contrast", "The printer produces pages quickly",
     "its ink costs run unusually high"),
    ("addition", "The trailhead gained a parking lot last spring",
     "rangers added restrooms at the summit"),
    ("consequence", "The storm knocked out the harbor lights",
     "ferry service paused until dawn"),
    ("contrast", "Critics call the plan ambitious",
     "few deny that its goals are reachable"),
    ("addition", "The bakery now ships statewide",
     "it still sells out most mornings downtown"),
    ("consequence", "Enrollment exceeded all projections",
     "two portable classrooms arrived by August"),
    ("contrast", "The recipe uses only pantry staples",
     "shoppers often make special trips for its saffron"),
]

SYNTHESIS_FACTS = [
    {"subject": "Juniper Labs", "year1": 2009, "product": "water filter",
     "award": "Green Prize", "year2": 2021},
    {"subject": "Harbor Robotics", "year1": 2015, "product": "dock crane",
     "award": "Innovation Medal", "year2": 2023},
    {"subject": "Bluebird Press", "year1": 2011, "product": "large-print readers",
     "award": "Literacy Award", "year2": 2020},
    {"subject": "Cedarline Optics", "year1": 2013, "product": "trail binoculars",
     "award": "Designers' Circle Prize", "year2": 2022},
    {"subject": "Mossgrove Farms", "year1": 2016, "product": "drought-tolerant barley",
     "award": "Soil Stewardship Medal", "year2": 2024},
    {"subject": "Lantern Audio", "year1": 2010, "product": "classroom listening kits",
     "award": "Access Prize", "year2": 2019},
    {"subject": "Quarry Street Games", "year1": 2018, "product": "cooperative board game",
     "award": "Playmakers Award", "year2": 2025},
    {"subject": "Northgate Mapping", "year1": 2012, "product": "flood-risk atlas",
     "award": "Civic Data Prize", "year2": 2021},
]


def _pick_frame(rng, difficulty):
    pool = WIC_FRAMES.get(difficulty)
    if not pool:
        pool = WIC_FRAMES["easy"]
    return rng.choice(pool)


def gen_words_in_context(rng, difficulty):
    frame = _pick_frame(rng, difficulty)
    correct = frame["answer"]
    choices, idx = build_choices(rng, correct, frame["distractors"])
    return {"prompt": frame["text"], "choices": list(choices), "answer_index": idx,
            "explanation": frame["explanation"]}


def gen_text_structure_purpose(rng, difficulty):
    eligible = [p for p in PURPOSE_PASSAGES if p["tier"] == difficulty] or \
               [p for p in PURPOSE_PASSAGES if p["tier"] == "easy"]
    item = rng.choice(eligible)
    choices, idx = build_choices(rng, item["correct"], item["distractors"])
    prompt = item["passage"] + "\n\nWhich choice best states the main purpose of the text?"
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": ("The text advances a claim or description and supports it; "
                            "the other options describe structures or goals the text "
                            "does not pursue.")}


def gen_cross_text_connections(rng, difficulty):
    eligible = [e for e in CTC_ENTRIES if e["tier"] == difficulty] or CTC_ENTRIES
    entry = rng.choice(eligible)
    stance = rng.choice(list(entry["stances"].keys()))
    text2 = entry["stances"][stance]
    descriptors = {
        "supports": "by citing evidence consistent with Text 1's claim",
        "contradicts": "by presenting a result that goes against Text 1's claim",
        "complicates": "by showing that Text 1's claim holds only in part",
    }
    correct = f"It responds to Text 1 {descriptors[stance]}"
    distract_map = [k for k in descriptors if k != stance]
    distractors = [f"It responds to Text 1 {descriptors[k]}" for k in distract_map]
    distractors.append("It restates Text 1 without adding any new information")
    prompt = (f"Text 1: {entry['text1']}\nText 2: {text2}\n\nBased on the texts, how "
              f"does the author of Text 2 respond to the claim in Text 1?")
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": f"Text 2 {stance} Text 1: {descriptors[stance][3:]}."}


def gen_central_ideas_details(rng, difficulty):
    eligible = [i for i in MAIN_IDEA_ITEMS if i["tier"] == difficulty] or MAIN_IDEA_ITEMS
    item = rng.choice(eligible)
    correct = item["correct"]
    distractors = [item["not_stated"], item["too_narrow"], item["contradicts"]]
    prompt = item["passage"] + "\n\nWhich choice best states the main idea of the text?"
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": ("The main idea covers the whole passage; one option is a "
                            "single supporting detail, one introduces information the "
                            "text never states, and one conflicts with the text.")}


def gen_command_of_evidence(rng, difficulty):
    topic = rng.choice(CLAIM_EVIDENCE_TOPICS)
    n = rng.randrange(20, 60, 2)
    gap = rng.randint(4, 9)
    hi = rng.randint(72, 84)
    lo = hi - gap
    correct = topic["support"](n, hi, lo)
    distractors = [fn(n, hi, lo) for fn in topic["wrong_kinds"]]
    prompt = (f"Researcher's claim: {topic['claim']}\n\nWhich finding, if true, would "
              f"most directly support the researcher's claim?")
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": ("Direct support must link the claimed behavior to the "
                            "claimed outcome with relevant measurements; the wrong "
                            "options address preference, cost, or unrelated measures.")}


def gen_inferences(rng, difficulty):
    eligible = [i for i in INFERENCE_ITEMS if i["tier"] == difficulty] or INFERENCE_ITEMS
    item = rng.choice(eligible)
    correct = item["correct"]
    prompt = item["passage"] + "\n\nWhich choice must be true according to the text?"
    choices, idx = build_choices(rng, correct, item["wrongs"])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": ("Only one option follows necessarily from the stated "
                            "facts; the others contradict a fact, overstate it, or "
                            "introduce information the text does not give.")}


def gen_sentence_boundaries(rng, difficulty):
    a, b = rng.choice(BOUNDARY_CLAUSES)
    b_lower = b[0].lower() + b[1:]
    correct = f"{a}; {b}."
    distractors = [f"{a}, {b}.", f"{a} {b}", f"{a}. {b_lower}."]
    prompt = (f"Which choice correctly joins these two independent clauses into one "
              f"grammatical sentence?\nClause 1: \"{a}\"\nClause 2: \"{b}\"")
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": ("Two independent clauses cannot be joined by only a comma "
                            "(a comma splice) or by nothing (a fused sentence); a "
                            "semicolon joins them correctly, and a sentence may not "
                            "begin with a lowercase letter.")}


def gen_form_structure_sense(rng, difficulty):
    verb_set = rng.choice(INFINITIVE_VERBS)
    subject = rng.choice(AGREEMENT_SUBJECTS)
    base, gerund, past, third = verb_set
    correct = base
    distractors = [gerund, past, third]
    prompt = (f"Facing a budget shortfall, {subject} voted to ______ the construction "
              f"deadline by six months.\n\nWhich choice completes the text so that it "
              f"conforms to the conventions of Standard English?")
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": ("After 'to' used as an infinitive marker, English requires "
                            f"the base verb form '{base}', not a participle or a "
                            "conjugated form.")}


def gen_transitions(rng, difficulty):
    relation, first, second = rng.choice(TRANSITION_SETS)
    connectors = RELATION_CONNECTORS
    correct = rng.choice(connectors[relation])
    other = []
    for rel, words in connectors.items():
        if rel != relation:
            other.extend(words)
    rng.shuffle(other)
    distractors = other[:3]
    prompt = (f"{first.capitalize()}; ______, {second}.\n\nWhich transition best fits "
              f"the relationship between the two clauses?")
    choices, idx = build_choices(rng, correct, distractors)
    relation_desc = {
        "consequence": "the second clause is a result of the first",
        "contrast": "the second clause contrasts with the first",
        "addition": "the second clause adds related information",
    }[relation]
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": f"{relation_desc.capitalize()}, so a {relation} transition "
                           f"such as '{correct}' is required; the other options signal "
                           "different relationships."}


def gen_rhetorical_synthesis(rng, difficulty):
    fact = rng.choice(SYNTHESIS_FACTS)
    notes = (f"\u2022 Company: {fact['subject']}\n"
             f"\u2022 Founded: {fact['year1']}\n"
             f"\u2022 First product: {fact['product']}\n"
             f"\u2022 Award won: {fact['award']} in {fact['year2']}")
    goal = "emphasize recognition of the company"
    correct = (f"Won the {fact['award']} in {fact['year2']}, {fact['subject']} is "
               f"recognized for the {fact['product']} it introduced after its "
               f"founding in {fact['year1']}.")
    distractors = [
        f"{fact['subject']} was founded in {fact['year1']} and makes the "
        f"{fact['product']}.",
        f"The {fact['product']} made by {fact['subject']} has been produced since "
        f"{fact['year2']}.",
        f"Awards such as the {fact['award']} existed well before {fact['year1']}.",
    ]
    prompt = (f"While researching a topic, a student has taken the following notes:\n"
              f"{notes}\n\nThe student wants to {goal}. Which choice most effectively "
              f"uses information from the notes to accomplish this goal?")
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": ("The goal requires foregrounding the award; only the "
                            "selected option leads with it while keeping the other "
                            "note facts accurate.")}


RW_GENERATORS = {
    "words_in_context": gen_words_in_context,
    "text_structure_purpose": gen_text_structure_purpose,
    "cross_text_connections": gen_cross_text_connections,
    "central_ideas_details": gen_central_ideas_details,
    "command_of_evidence": gen_command_of_evidence,
    "inferences": gen_inferences,
    "sentence_boundaries": gen_sentence_boundaries,
    "form_structure_sense": gen_form_structure_sense,
    "transitions": gen_transitions,
    "rhetorical_synthesis": gen_rhetorical_synthesis,
}


def generate(skill_id: str, rng, difficulty: str) -> dict:
    gen = RW_GENERATORS.get(skill_id)
    if gen is None:
        raise KeyError(skill_id)
    return gen(rng, difficulty)
