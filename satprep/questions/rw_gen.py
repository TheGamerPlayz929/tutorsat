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
     "text1": ("Adding protected bike lanes downtown will reduce traffic injuries. "
               "City planners point to data from other municipalities showing "
               "consistent declines in cyclist-involved crashes."),
     "stances": {
         "supports": ("Cities that installed protected lanes saw injury rates fall "
                      "within two years. A five-year study of twenty cities "
                      "confirmed the trend held across different street layouts."),
         "contradicts": ("Injury rates on our city's Main Street rose after "
                         "protected lanes were installed there. Local officials "
                         "attribute the increase to drivers unfamiliar with the "
                         "new configuration."),
         "complicates": ("Protected lanes reduced car-bike collisions on some "
                         "streets but increased them at intersections. The "
                         "intersection effect was strongest where turn lanes "
                         "were not added alongside the protected lanes.")}},
    {"tier": "easy",
     "text1": ("Later school start times improve student alertness. Research "
               "suggests adolescents need more sleep than early bell schedules "
               "allow."),
     "stances": {
         "supports": ("Students at schools that delayed start times reported "
                      "feeling less sleepy during morning classes. Teachers "
                      "noted increased participation in first-period discussions."),
         "contradicts": ("A large survey found no change in student alertness "
                         "after start times shifted later. Many students simply "
                         "stayed up later, negating the potential sleep gain."),
         "complicates": ("Alertness improved for older teens but declined for "
                         "students with long bus commutes. Those students had "
                         "to wake even earlier to catch revised bus schedules.")}},
    {"tier": "medium",
     "text1": ("Common houseplants meaningfully improve indoor air quality. "
               "Proponents cite NASA chamber studies from the 1980s showing "
               "plants absorb volatile organic compounds."),
     "stances": {
         "supports": ("Chamber studies show several common houseplants absorb "
                      "certain airborne compounds. Peace lilies and snake "
                      "plants were among the most effective species tested."),
         "contradicts": ("Building-scale tests find plants remove far too little "
                         "of these compounds to matter. The chamber conditions "
                         "did not reflect real-room air exchange rates."),
         "complicates": ("Houseplants filter some chemicals effectively while "
                         "doing almost nothing for others. Benzene absorption "
                         "was strong, but formaldehyde removal was negligible "
                         "in typical room volumes.")}},
    {"tier": "medium",
     "text1": ("Four-day workweeks raise employee productivity. Companies "
               "adopting the schedule report maintained or increased output "
               "with fewer work hours."),
     "stances": {
         "supports": ("Trial firms produced the same output in four days as "
                      "they had in five. Employees eliminated low-value "
                      "meetings and compressed focused work into core hours."),
         "contradicts": ("Weekly output fell at firms that cut to four days "
                         "without reducing total workload. The same tasks "
                         "simply took longer when compressed."),
         "complicates": ("Productivity rose for office roles but did not "
                         "improve in shift-based roles. Manufacturing and "
                         "service teams saw no gains from the compressed week.")}},
    {"tier": "easy",
     "text1": ("School gardens increase children's vegetable intake. Hands-on "
               "growing experiences make students more willing to try the "
               "produce they helped cultivate."),
     "stances": {
         "supports": ("Students at schools with gardens reported eating more "
                      "vegetables each week. Cafeteria data confirmed higher "
                      "salad-bar selection on garden-harvest days."),
         "contradicts": ("Intake surveys showed no difference between garden "
                         "and non-garden schools. The garden effect did not "
                         "persist through summer break."),
         "complicates": ("Garden students ate more vegetables at school but "
                         "not at home. The increase was limited to meals where "
                         "garden produce was served directly.")}},
    {"tier": "medium",
     "text1": ("Cities should convert vacant lots into pocket parks. Small "
               "green spaces can revitalize neighborhoods at relatively low "
               "cost."),
     "stances": {
         "supports": ("Neighborhoods that added pocket parks reported rising "
                      "resident satisfaction. Property values near new parks "
                      "increased modestly within two years."),
         "contradicts": ("Several converted lots fell into disrepair because "
                         "upkeep lapsed after opening. Municipal maintenance "
                         "budgets did not account for the new acreage."),
         "complicates": ("Pocket parks lifted satisfaction on quiet streets "
                         "while drawing noise complaints on busy ones. Evening "
                         "use patterns differed sharply by surrounding land use.")}},
    {"tier": "hard",
     "text1": ("Automated essay scoring is reliable enough for college "
               "placement decisions. Machine learning models now match human "
               "readers on holistic rubric scores."),
     "stances": {
         "supports": ("On double-scored samples, machine-human agreement "
                      "matches human-human agreement. The system processes "
                      "thousands of essays in minutes without fatigue."),
         "contradicts": ("Adversarial essays padded with sophisticated "
                         "gibberish earned passing machine scores. The models "
                         "rewarded vocabulary and length over coherence."),
         "complicates": ("The software agrees with human readers on structure "
                         "but penalizes unconventional yet valid arguments. "
                         "Creative rhetorical choices were scored lower than "
                         "formulaic five-paragraph templates.")}},
    {"tier": "hard",
     "text1": ("Four-day school weeks harm student achievement. Compressing "
               "instructional time into fewer days reduces learning "
               "opportunities."),
     "stances": {
         "supports": ("Test scores dipped in districts after the switch to "
                      "four days. The decline was most pronounced in math "
                      "and among younger students."),
         "contradicts": ("Districts on four-day weeks matched five-day "
                         "districts' scores. Longer daily blocks allowed "
                         "deeper project-based work."),
         "complicates": ("Scores held steady overall but fell for students "
                         "without reliable home internet. Those students lost "
                         "the fifth day of school-based connectivity.")}},
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
     "context": ("Researchers surveyed elementary and middle schools across three "
                 "districts, comparing morning test performance between students who "
                 "ate breakfast at home or school and those who did not."),
     "claim": "Students who eat breakfast before school perform better on morning tests.",
     "support": lambda n, hi, lo: (
         f"In a study of {n} schools, students who ate breakfast averaged {hi}% on "
         f"morning tests compared with {lo}% among students who skipped breakfast."),
     "wrong_kinds": [
         lambda n, hi, lo: f"Students reported that breakfast foods taste better than vending-machine snacks.",
         lambda n, hi, lo: f"Afternoon test scores were nearly identical across breakfast habits.",
         lambda n, hi, lo: f"Breakfast programs cost schools about two dollars per student per week."]},
    {"tier": "medium",
     "context": ("A cognitive science lab placed identical desk plants in half of "
                 "the workstations in an open-plan office. Over six weeks, employees "
                 "completed timed proofreading tasks at their desks."),
     "claim": "Office workers focus better when plants are visible at their desks.",
     "support": lambda n, hi, lo: (
         f"Across {n} offices, workers with desk plants completed a proofreading task "
         f"{hi - lo}% faster than workers without them."),
     "wrong_kinds": [
         lambda n, hi, lo: f"Most workers said they prefer plants to posters when decorating.",
         lambda n, hi, lo: f"Plants reduced measured noise levels slightly in open offices.",
         lambda n, hi, lo: f"The most common desk plants cost under ten dollars each."]},
    {"tier": "medium",
     "context": ("A police department partnered with neighborhood associations to "
                 "install watch signs on randomly selected blocks. Crime reports were "
                 "tracked for eighteen months before and after installation."),
     "claim": "Neighborhood watch signs reduce daytime break-ins.",
     "support": lambda n, hi, lo: (
         f"Blocks displaying {n} new signs saw reported daytime break-ins fall to "
         f"{lo} per year, down from {hi}, while sign-free blocks stayed flat."),
     "wrong_kinds": [
         lambda n, hi, lo: f"Residents on signed blocks said they feel safer walking at night.",
         lambda n, hi, lo: f"The average sign costs about forty dollars to produce and install.",
         lambda n, hi, lo: f"Nighttime break-ins fell across the whole city during the study."]},
    {"tier": "hard",
     "context": ("A university sleep lab recruited varsity basketball players for a "
                 "two-week protocol. Baseline free-throw percentages were recorded, "
                 "then players added ninety minutes to their nightly sleep."),
     "claim": "Extending sleep improves free-throw accuracy in young basketball players.",
     "support": lambda n, hi, lo: (
         f"Players who extended sleep for {n} nights made {hi}% of free throws in "
         f"post-tests, up from a {lo}% baseline measured beforehand."),
     "wrong_kinds": [
         lambda n, hi, lo: f"Players reported enjoying later wake times during the extension period.",
         lambda n, hi, lo: f"Taller players tended to have higher shooting percentages overall.",
         lambda n, hi, lo: f"Practice minutes per week were similar across all players studied."]},
    {"tier": "hard",
     "context": ("A consumer-safety lab tested warning-label formats with adults "
                 "who read product information in either a single language or a "
                 "bilingual format. Recall was measured after a short delay."),
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
     "passage": ("The Cedar Grove gallery displays paintings only from Tuesday "
                 "through Saturday. Admission is free on Wednesdays. The gallery "
                 "closes each evening at 6 p.m., but on the first Friday of each "
                 "month it stays open until 9 p.m. for a reception."),
     "correct": "A visitor who wants free admission should go on a Wednesday.",
     "wrongs": ["The gallery is open every day of the week.",
                "Admission is always free at the gallery.",
                "The gallery displays sculptures as well as paintings."]},
    {"tier": "easy",
     "passage": ("The Willow Creek plant nursery refunds any tree that fails to "
                 "leaf out by June 1. The nursery closes every Sunday. Customers "
                 "who purchase a tree in March can return it for a full refund "
                 "through the end of May if it has not leafed out."),
     "correct": "A customer cannot buy a refund-eligible tree there on a Sunday.",
     "wrongs": ["The nursery sells only trees.",
                "Refunds require a written request.",
                "The nursery opens late on Sundays."]},
    {"tier": "easy",
     "passage": ("The Millstone bakery sells rye bread only on Fridays and "
                 "Saturdays. On Saturdays, the bakery closes at noon. The rye "
                 "loaves typically sell out within an hour of opening."),
     "correct": "On some days the bakery sells rye bread before noon.",
     "wrongs": ["Rye bread sells out before noon on Fridays.",
                "The bakery closes at noon on both Friday and Saturday.",
                "The bakery sells rye bread on Sundays."]},
    {"tier": "medium",
     "passage": ("Every locker in Row C of the downtown station opens with a "
                 "physical key, not a code. Over winter break, exactly half of "
                 "the Row C keys were replaced with new ones. The station manager "
                 "kept the original keys in a locked drawer in the office."),
     "correct": "At least some lockers in Row C use keys made before winter break.",
     "wrongs": ["No locker in Row C opens with a key.",
                "Every key for Row C was replaced over winter break.",
                "Some lockers in Row C open with codes."]},
    {"tier": "medium",
     "passage": ("The campus shuttle runs between the north and south campuses "
                 "every twenty minutes. The first shuttle leaves the north campus "
                 "at 7:10 a.m. Service continues until the final departure at "
                 "10:50 p.m. from the south campus."),
     "correct": "A shuttle departs the north campus at 7:30 a.m.",
     "wrongs": ["Shuttles leave both campuses at 7:10 a.m.",
                "The shuttle runs every twelve minutes.",
                "The last shuttle leaves after midnight."]},
    {"tier": "medium",
     "passage": ("Members who join the Ridgeview club after March pay a reduced "
                 "initiation fee, but every member pays the same annual dues "
                 "each January. The dues cover access to the pool, courts, and "
                 "fitness center. Late payments incur a small administrative fee."),
     "correct": "Two members who joined in different years pay the same January dues.",
     "wrongs": ["Members who joined earliest pay lower annual dues.",
                "The initiation fee is refunded every January.",
                "No member pays an initiation fee."]},
    {"tier": "hard",
     "passage": ("Every novel on the library's special-collections shelf is "
                 "either historical fiction or a mystery. All the mysteries were "
                 "published after 1990, but some historical fiction dates from "
                 "earlier decades. The collection was curated to show the "
                 "evolution of both genres over time."),
     "correct": "Any book on the shelf published before 1990 is historical fiction.",
     "wrongs": ["Some mysteries on the shelf were published before 1990.",
                "Every historical novel on the shelf was published after 1990.",
                "No book on the shelf combines history and mystery elements."]},
    {"tier": "hard",
     "passage": ("Of the five speakers scheduled for the symposium, three "
                 "discuss geology and no two talks overlap. The two non-geology "
                 "talks run back to back in the afternoon session. A moderator "
                 "introduces each speaker and fields audience questions."),
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

COMPLEX_SUBJECTS = [
    "the committee members along with the chair",
    "neither the director nor the assistants",
    "the data and the analysis",
    "either the proposal or the amendments",
    "a variety of factors",
    "the number of applicants",
    "the majority of the board",
    "each of the proposals",
]

AGREEMENT_VERBS = [
    ("approve", "approves"),
    ("reject", "rejects"),
    ("support", "supports"),
    ("oppose", "opposes"),
    ("review", "reviews"),
    ("modify", "modifies"),
    ("delay", "delays"),
    ("accept", "accepts"),
]

TENSE_TEMPLATES = [
    {
        "prompt": ("By the time the committee ______ its report, the deadline "
                   "will have passed.\n\nWhich choice completes the text so that it "
                   "conforms to the conventions of Standard English?"),
        "correct": "submits",
        "wrongs": ["submit", "submitted", "will submit"],
        "expl": ("Future perfect 'will have passed' sets a future reference point; "
                 "the subordinate clause requires present tense 'submits' to indicate "
                 "an action completed before that future moment.")
    },
    {
        "prompt": ("Had the board ______ the amendment earlier, the vote "
                   "would have proceeded differently.\n\nWhich choice completes the text so that it "
                   "conforms to the conventions of Standard English?"),
        "correct": "reviewed",
        "wrongs": ["review", "reviews", "reviewing"],
        "expl": ("Counterfactual past perfect requires 'had + past participle' "
                 "('had reviewed'); the other forms create tense mismatches.")
    },
    {
        "prompt": ("The analyst recommended that the policy ______ immediately.\n\n"
                   "Which choice completes the text so that it conforms to "
                   "the conventions of Standard English?"),
        "correct": "be implemented",
        "wrongs": ["is implemented", "implements", "implemented"],
        "expl": ("Mandative subjunctive after 'recommended that' requires "
                 "bare infinitive 'be implemented'; indicative forms are ungrammatical here.")
    },
    {
        "prompt": ("Not only ______ the data support the hypothesis, but it "
                   "also suggests a new mechanism.\n\nWhich choice completes the text so that it "
                   "conforms to the conventions of Standard English?"),
        "correct": "does",
        "wrongs": ["do", "did", "doing"],
        "expl": ("Inversion with 'not only' requires auxiliary 'does' for singular "
                 "subject 'the data' (treated as singular in formal usage); 'do' would "
                 "be plural agreement.")
    },
]

RELATION_CONNECTORS = {
    "consequence": ["consequently", "therefore", "as a result"],
    "contrast": ["however", "nevertheless", "by contrast"],
    "addition": ["moreover", "furthermore", "likewise"],
    "concession": ["nevertheless", "even so", "still"],
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

CONCESSION_SETS = [
    ("The admission fee is undeniably steep", "the concert sold out within hours"),
    ("The hike demands eight hours of steady climbing", "families with young children attempt it every weekend"),
    ("The diner sits well off the main highway", "its booths are full every Sunday morning"),
    ("The novel runs past six hundred pages", "it reads quickly from the first chapter"),
    ("The software requires a subscription", "the library offers it free to every cardholder"),
    ("The theater seats fewer than ninety people", "its productions routinely sell out"),
    ("The course meets at seven in the morning", "its enrollment list is the longest in the department"),
    ("The shop closes at three in the afternoon", "customers line up before it opens"),
]

COLON_ITEMS = [
    ("The festival imposes one strict requirement on its food vendors",
     "all ingredients must be sourced within the county"),
    ("The committee's final report rested on a single conclusion",
     "the bridge could not be repaired at any reasonable cost"),
    ("The museum's newest wing was built around one centerpiece",
     "a restored locomotive from the city's first rail line"),
    ("The coach's halftime talk conveyed a simple message",
     "the second half would belong to whoever wanted it more"),
    ("The scholarship fund honors one core belief",
     "financial need should never decide who attends college"),
    ("The town's water ban left residents with one option",
     "gardens would have to survive on saved rainwater"),
    ("The expedition carried one non-negotiable rule",
     "no member ever hiked the final stretch alone"),
    ("The archive's donation came with a single condition",
     "the letters would remain sealed until 2050"),
]

TRANSITION_PARAGRAPHS = {
    "easy": [
        {"before": "Researchers studying the valley's agriculture have found that the soil is thin and nutrient-poor.",
         "first": "the soil lacks essential minerals",
         "second": "farmers there have long relied on imported fertilizer",
         "after": "Recent soil analyses confirm the dependency.",
         "correct": "therefore",
         "wrongs": ["however", "moreover", "nevertheless"]},
        {"before": "Winter tourism keeps the mountain town busy through February.",
         "first": "hotels and restaurants operate at full capacity",
         "second": "the months of March and April remain quiet",
         "after": "Local businesses plan their staffing around this pattern.",
         "correct": "by contrast",
         "wrongs": ["therefore", "moreover", "as a result"]},
        {"before": "The new library branch offers free tutoring on weekdays.",
         "first": "students receive help with core subjects",
         "second": "it hosts weekend coding clubs for teenagers",
         "after": "Both programs are funded by the municipal grant.",
         "correct": "moreover",
         "wrongs": ["however", "therefore", "nevertheless"]},
        {"before": "The old bridge closed for repairs last spring.",
         "first": "the main route across the river was severed",
         "second": "commuters faced long detours for six weeks",
         "after": "Traffic patterns still show the impact today.",
         "correct": "as a result",
         "wrongs": ["however", "moreover", "by contrast"]},
        {"before": "Demand for the introductory course doubled this year.",
         "first": "waitlists grew beyond the department's capacity",
         "second": "the department hired a second instructor",
         "after": "Class sizes have returned to manageable levels.",
         "correct": "consequently",
         "wrongs": ["however", "furthermore", "by contrast"]},
        {"before": "The reservoir dropped below half capacity in July.",
         "first": "water levels reached a twenty-year low",
         "second": "the city banned lawn watering through September",
         "after": "Rainfall in October finally restored normal levels.",
         "correct": "therefore",
         "wrongs": ["however", "moreover", "by contrast"]},
    ],
    "medium": [
        {"before": "The printer produces pages quickly and quietly.",
         "first": "it handles large jobs without jamming",
         "second": "its ink costs run unusually high",
         "after": "Budget-conscious departments limit color printing.",
         "correct": "however",
         "wrongs": ["therefore", "moreover", "as a result"]},
        {"before": "The trailhead gained a parking lot last spring.",
         "first": "access to the popular loop trail improved",
         "second": "rangers added restrooms at the summit",
         "after": "Visitor numbers have increased each month since.",
         "correct": "additionally",
         "wrongs": ["therefore", "however", "nevertheless"]},
        {"before": "The storm knocked out the harbor lights.",
         "first": "navigation became dangerous after dark",
         "second": "ferry service paused until dawn",
         "after": "No vessels were damaged during the outage.",
         "correct": "consequently",
         "wrongs": ["however", "furthermore", "by contrast"]},
        {"before": "Critics call the redevelopment plan ambitious.",
         "first": "the timeline alone spans a decade",
         "second": "few deny that its goals are reachable",
         "after": "The city council approved funding unanimously.",
         "correct": "nevertheless",
         "wrongs": ["therefore", "moreover", "as a result"]},
        {"before": "The bakery now ships its signature bread statewide.",
         "first": "online orders arrive from across the region",
         "second": "it still sells out most mornings downtown",
         "after": "Local customers arrive before opening to secure a loaf.",
         "correct": "even so",
         "wrongs": ["therefore", "moreover", "as a result"]},
        {"before": "Enrollment exceeded all projections for the fall term.",
         "first": "the freshman class alone grew by twelve percent",
         "second": "two portable classrooms arrived by August",
         "after": "The district plans a permanent addition next year.",
         "correct": "accordingly",
         "wrongs": ["however", "nevertheless", "by contrast"]},
    ],
    "hard": [
        {"before": "The recipe uses only pantry staples and takes twenty minutes.",
         "first": "the ingredient list is surprisingly short",
         "second": "shoppers often make special trips for its saffron",
         "after": "The spice accounts for most of the dish's cost.",
         "correct": "nevertheless",
         "wrongs": ["therefore", "furthermore", "as a result"]},
        {"before": "Automated scoring matches human readers on holistic rubrics.",
         "first": "the models process thousands of essays in minutes",
         "second": "adversarial essays padded with gibberish earned passing scores",
         "after": "The discrepancy has prompted calls for human review.",
         "correct": "however",
         "wrongs": ["therefore", "moreover", "consequently"]},
        {"before": "Four-day school weeks maintain overall test scores.",
         "first": "longer daily blocks allow deeper project work",
         "second": "scores fell for students without reliable home internet",
         "after": "Equity concerns have stalled statewide adoption.",
         "correct": "yet",
         "wrongs": ["therefore", "moreover", "consequently"]},
        {"before": "The software requires a subscription for full functionality.",
         "first": "the professional tier costs hundreds per year",
         "second": "the library offers it free to every cardholder",
         "after": "Patrons save hundreds annually on design tools.",
         "correct": "still",
         "wrongs": ["therefore", "moreover", "as a result"]},
        {"before": "Houseplants absorb certain airborne compounds in sealed chambers.",
         "first": "chamber studies show measurable uptake of VOCs",
         "second": "building-scale tests find plants remove far too little to matter",
         "after": "Real-room air exchange overwhelms the plants' capacity.",
         "correct": "however",
         "wrongs": ["therefore", "furthermore", "consequently"]},
        {"before": "Weekly output fell at firms that cut to four days without reducing workload.",
         "first": "employees reported higher stress and fatigue",
         "second": "the same tasks simply took longer when compressed",
         "after": "Productivity gains require workload redesign, not just schedule changes.",
         "correct": "in fact",
         "wrongs": ["therefore", "however", "nevertheless"]},
    ],
}

BOUNDARY_PARAGRAPHS = {
    "easy": [
        {"text": ("The bakery opens at dawn; its ovens glow before sunrise. "
                  "The first customers arrive by 6 a.m."),
         "blank_pos": 1,
         "first": "The bakery opens at dawn",
         "second": "its ovens glow before sunrise",
         "correct": "The bakery opens at dawn; its ovens glow before sunrise.",
         "wrongs": ["The bakery opens at dawn, its ovens glow before sunrise.",
                    "The bakery opens at dawn its ovens glow before sunrise.",
                    "The bakery opens at dawn. Its ovens glow before sunrise."],
         "expl": "Two independent clauses joined by a semicolon; a comma alone creates a comma splice."},
        {"text": ("The ferry leaves every hour; the dock fills up quickly. "
                  "Weekend lines stretch down the pier."),
         "blank_pos": 1,
         "first": "The ferry leaves every hour",
         "second": "the dock fills up quickly",
         "correct": "The ferry leaves every hour; the dock fills up quickly.",
         "wrongs": ["The ferry leaves every hour, the dock fills up quickly.",
                    "The ferry leaves every hour the dock fills up quickly.",
                    "The ferry leaves every hour. The dock fills up quickly."],
         "expl": "A semicolon correctly joins two independent clauses; a comma splice or fused sentence is incorrect."},
        {"text": ("Rain flooded the lower field; the festival moved to the "
                  "gymnasium. Attendance was unaffected."),
         "blank_pos": 1,
         "first": "Rain flooded the lower field",
         "second": "the festival moved to the gymnasium",
         "correct": "Rain flooded the lower field; the festival moved to the gymnasium.",
         "wrongs": ["Rain flooded the lower field, the festival moved to the gymnasium.",
                    "Rain flooded the lower field the festival moved to the gymnasium.",
                    "Rain flooded the lower field. The festival moved to the gymnasium."],
         "expl": "The semicolon joins two independent clauses; a comma alone is insufficient."},
        {"text": ("Volunteers repainted the community center; neighbors "
                  "donated most of the supplies. The project finished in a "
                  "weekend."),
         "blank_pos": 1,
         "first": "Volunteers repainted the community center",
         "second": "neighbors donated most of the supplies",
         "correct": "Volunteers repainted the community center; neighbors donated most of the supplies.",
         "wrongs": ["Volunteers repainted the community center, neighbors donated most of the supplies.",
                    "Volunteers repainted the community center neighbors donated most of the supplies.",
                    "Volunteers repainted the community center. Neighbors donated most of the supplies."],
         "expl": "Two independent clauses require a semicolon (or period), not a comma."},
    ],
    "medium": [
        {"text": ("The trail switchbacks up the ridge; however, hikers gain "
                  "a thousand feet by lunchtime. The view from the top rewards "
                  "every step."),
         "blank_pos": 1,
         "first": "The trail switchbacks up the ridge",
         "second": "hikers gain a thousand feet by lunchtime",
         "correct": "The trail switchbacks up the ridge; however, hikers gain a thousand feet by lunchtime.",
         "wrongs": ["The trail switchbacks up the ridge, however, hikers gain a thousand feet by lunchtime.",
                    "The trail switchbacks up the ridge; however hikers gain a thousand feet by lunchtime.",
                    "The trail switchbacks up the ridge, however hikers gain a thousand feet by lunchtime."],
         "expl": "A semicolon plus a conjunctive adverb ('however') and a comma correctly joins independent clauses; a comma alone or missing comma after 'however' is incorrect."},
        {"text": ("The observatory opens to the public on Fridays; therefore, "
                  "volunteers staff the telescopes. Clear skies draw the "
                  "largest crowds."),
         "blank_pos": 1,
         "first": "The observatory opens to the public on Fridays",
         "second": "volunteers staff the telescopes",
         "correct": "The observatory opens to the public on Fridays; therefore, volunteers staff the telescopes.",
         "wrongs": ["The observatory opens to the public on Fridays, therefore, volunteers staff the telescopes.",
                    "The observatory opens to the public on Fridays; therefore volunteers staff the telescopes.",
                    "The observatory opens to the public on Fridays, therefore volunteers staff the telescopes."],
         "expl": "A semicolon before the conjunctive adverb 'therefore' and a comma after it is the standard pattern; a comma splice or missing comma is incorrect."},
        {"text": ("Snow closed the mountain pass; nevertheless, mail trucks "
                  "took the valley route. Deliveries arrived only hours late."),
         "blank_pos": 1,
         "first": "Snow closed the mountain pass",
         "second": "mail trucks took the valley route",
         "correct": "Snow closed the mountain pass; nevertheless, mail trucks took the valley route.",
         "wrongs": ["Snow closed the mountain pass, nevertheless, mail trucks took the valley route.",
                    "Snow closed the mountain pass; nevertheless mail trucks took the valley route.",
                    "Snow closed the mountain pass, nevertheless mail trucks took the valley route."],
         "expl": "A semicolon plus conjunctive adverb ('nevertheless') with a comma is correct; a comma splice or missing comma is not."},
        {"text": ("The choir rehearses in the library basement; moreover, the "
                  "acoustics surprise first-time visitors. The space was "
                  "designed for lectures."),
         "blank_pos": 1,
         "first": "The choir rehearses in the library basement",
         "second": "the acoustics surprise first-time visitors",
         "correct": "The choir rehearses in the library basement; moreover, the acoustics surprise first-time visitors.",
         "wrongs": ["The choir rehearses in the library basement, moreover, the acoustics surprise first-time visitors.",
                    "The choir rehearses in the library basement; moreover the acoustics surprise first-time visitors.",
                    "The choir rehearses in the library basement, moreover the acoustics surprise first-time visitors."],
         "expl": "A semicolon before and a comma after the conjunctive adverb 'moreover' correctly joins the clauses."},
    ],
    "hard": [
        {"text": ("The festival imposes one strict requirement on its food "
                  "vendors: all ingredients must be sourced within the county. "
                  "Local farms benefit from the guaranteed demand."),
         "blank_pos": 1,
         "first": "The festival imposes one strict requirement on its food vendors",
         "second": "all ingredients must be sourced within the county",
         "correct": "The festival imposes one strict requirement on its food vendors: all ingredients must be sourced within the county.",
         "wrongs": ["The festival imposes one strict requirement on its food vendors; all ingredients must be sourced within the county.",
                    "The festival imposes one strict requirement on its food vendors, all ingredients must be sourced within the county.",
                    "The festival imposes one strict requirement on its food vendors. All ingredients must be sourced within the county."],
         "expl": "A colon introduces an explanation that follows an independent clause; a semicolon or comma alone would incorrectly join a clause to a fragment."},
        {"text": ("The committee's final report rested on a single conclusion: "
                  "the bridge could not be repaired at any reasonable cost. "
                  "Replacement was the only viable option."),
         "blank_pos": 1,
         "first": "The committee's final report rested on a single conclusion",
         "second": "the bridge could not be repaired at any reasonable cost",
         "correct": "The committee's final report rested on a single conclusion: the bridge could not be repaired at any reasonable cost.",
         "wrongs": ["The committee's final report rested on a single conclusion; the bridge could not be repaired at any reasonable cost.",
                    "The committee's final report rested on a single conclusion, the bridge could not be repaired at any reasonable cost.",
                    "The committee's final report rested on a single conclusion. The bridge could not be repaired at any reasonable cost."],
         "expl": "A colon correctly introduces the explanation following the independent clause; a semicolon or comma splice is incorrect."},
        {"text": ("The expedition carried one non-negotiable rule: no member "
                  "ever hiked the final stretch alone. Safety depended on "
                  "the buddy system."),
         "blank_pos": 1,
         "first": "The expedition carried one non-negotiable rule",
         "second": "no member ever hiked the final stretch alone",
         "correct": "The expedition carried one non-negotiable rule: no member ever hiked the final stretch alone.",
         "wrongs": ["The expedition carried one non-negotiable rule; no member ever hiked the final stretch alone.",
                    "The expedition carried one non-negotiable rule, no member ever hiked the final stretch alone.",
                    "The expedition carried one non-negotiable rule. No member ever hiked the final stretch alone."],
         "expl": "A colon introduces the rule stated after the independent clause; a semicolon would wrongly join a clause to a fragment."},
        {"text": ("The archive's donation came with a single condition: the "
                  "letters would remain sealed until 2050. Scholars await "
                  "the unsealing eagerly."),
         "blank_pos": 1,
         "first": "The archive's donation came with a single condition",
         "second": "the letters would remain sealed until 2050",
         "correct": "The archive's donation came with a single condition: the letters would remain sealed until 2050.",
         "wrongs": ["The archive's donation came with a single condition; the letters would remain sealed until 2050.",
                    "The archive's donation came with a single condition, the letters would remain sealed until 2050.",
                    "The archive's donation came with a single condition. The letters would remain sealed until 2050."],
         "expl": "A colon introduces the condition specified after the independent clause; a semicolon or comma splice is incorrect."},
    ],
}

FSS_PARAGRAPHS = {
    "easy": [
        {"text": ("Facing a budget shortfall, the planning board voted to "
                  "______ the construction deadline by six months. The "
                  "extension gives contractors breathing room."),
         "correct": "extend",
         "wrongs": ["extending", "extended", "extends"],
         "expl": "After 'to' used as an infinitive marker, English requires the base verb form 'extend', not a participle or conjugated form."},
        {"text": ("To address the backlog, the committee decided to "
                  "______ all pending applications this week. Volunteers "
                  "will assist with the review."),
         "correct": "review",
         "wrongs": ["reviewing", "reviewed", "reviews"],
         "expl": "The infinitive 'to review' requires the base form; 'reviewing' is a participle and 'reviewed'/'reviews' are conjugated."},
        {"text": ("Because the venue was unavailable, the organizers had to "
                  "______ the event to next month. Ticket holders were "
                  "notified immediately."),
         "correct": "postpone",
         "wrongs": ["postponing", "postponed", "postpones"],
         "expl": "The modal phrase 'had to' takes the bare infinitive 'postpone'; other forms are ungrammatical here."},
        {"text": ("After the auditor's findings, the director agreed to "
                  "______ the budget projections. The revised numbers "
                  "reflect actual costs."),
         "correct": "revise",
         "wrongs": ["revising", "revised", "revises"],
         "expl": "The infinitive 'to revise' requires the base form 'revise'; 'revising' is a gerund and 'revised'/'revises' are conjugated."},
    ],
    "medium": [
        {"text": ("The committee members along with the chair ______ the "
                  "proposal after reviewing the data. Their support was "
                  "unanimous."),
         "correct": "approve",
         "wrongs": ["approves", "approves", "approved"],
         "expl": "The subject 'the committee members along with the chair' is plural (the phrase 'along with' does not change the number of the head noun 'members'), requiring the base verb form 'approve'."},
        {"text": ("Neither the director nor the assistants ______ the "
                  "recommendation. Only the board can authorize it."),
         "correct": "oppose",
         "wrongs": ["opposes", "oppose", "opposed"],
         "expl": "With 'neither...nor', the verb agrees with the closer subject 'assistants' (plural), so the base form 'oppose' is required."},
        {"text": ("The data and the analysis ______ the hypothesis. Further "
                  "studies will test the prediction."),
         "correct": "support",
         "wrongs": ["supports", "support", "supported"],
         "expl": "The compound subject 'the data and the analysis' is plural, taking the base verb form 'support'."},
        {"text": ("Either the proposal or the amendments ______ the "
                  "deadline. The committee will vote tomorrow."),
         "correct": "delay",
         "wrongs": ["delays", "delay", "delayed"],
         "expl": "With 'either...or', the verb agrees with the closer subject 'amendments' (plural), requiring the base form 'delay'."},
    ],
    "hard": [
        {"text": ("By the time the committee ______ its report, the "
                  "deadline will have passed. Extensions are not "
                  "permitted."),
         "correct": "submits",
         "wrongs": ["submit", "submitted", "will submit"],
         "expl": "Future perfect 'will have passed' sets a future reference point; the subordinate clause requires present tense 'submits' to indicate an action completed before that future moment."},
        {"text": ("Had the board ______ the amendment earlier, the vote "
                  "would have proceeded differently. The delay forced a "
                  "special session."),
         "correct": "reviewed",
         "wrongs": ["review", "reviews", "reviewing"],
         "expl": "Counterfactual past perfect requires 'had + past participle' ('had reviewed'); the other forms create tense mismatches."},
        {"text": ("The analyst recommended that the policy ______ "
                  "immediately. Implementation begins next quarter."),
         "correct": "be implemented",
         "wrongs": ["is implemented", "implements", "implemented"],
         "expl": "Mandative subjunctive after 'recommended that' requires bare infinitive 'be implemented'; indicative forms are ungrammatical here."},
        {"text": ("Not only ______ the data support the hypothesis, but it "
                  "also suggests a new mechanism. The findings are "
                  "statistically significant."),
         "correct": "does",
         "wrongs": ["do", "did", "doing"],
         "expl": "Inversion with 'not only' requires auxiliary 'does' for singular subject 'the data' (treated as singular in formal usage); 'do' would be plural agreement."},
    ],
}

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
    eligible = [t for t in CLAIM_EVIDENCE_TOPICS if t["tier"] == difficulty] or CLAIM_EVIDENCE_TOPICS
    topic = rng.choice(eligible)
    n = rng.randrange(20, 60, 2)
    gap = rng.randint(4, 9)
    hi = rng.randint(72, 84)
    lo = hi - gap
    correct = topic["support"](n, hi, lo)
    distractors = [fn(n, hi, lo) for fn in topic["wrong_kinds"]]
    prompt = (f"{topic['context']}\n\nResearcher's claim: {topic['claim']}\n\n"
              f"Which finding, if true, would most directly support the "
              f"researcher's claim?")
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
    pool = BOUNDARY_PARAGRAPHS.get(difficulty) or BOUNDARY_PARAGRAPHS["easy"]
    item = rng.choice(pool)
    # The item has "text" with the full paragraph, "correct" and "wrongs" as the
    # four options for how to join the clauses within the paragraph.
    # We present the full paragraph with a blank where the join occurs.
    # The item already has "correct" and "wrongs" as full sentence strings.
    # But we need to show the paragraph with a blank. Let me restructure:
    # The item has "text" = full correct paragraph, "correct" = the correct join,
    # "wrongs" = incorrect joins.
    # We'll present the paragraph with the joined part replaced by a blank.
    # Actually, simpler: the item already has the correct joined sentence as "correct"
    # and the paragraph context. We can present the paragraph with the two clauses
    # shown and a blank between them.
    # Looking at my data: each item has "first" and "second" clauses, and "correct"
    # is the properly joined version.
    # Let me present: the paragraph with the two clauses separated by "______"
    first = item["first"]
    second = item["second"]
    # Find the position in the text where first + join + second occurs
    # For simplicity, present the text with the join blanked
    # The "text" field contains the full correct paragraph
    # We'll replace the correct join with a blank
    correct_join = item["correct"]
    # Find the join in the text and replace with blank
    # The correct join is first + join_punct + " " + second (with capitalization)
    # For the prompt, we show the paragraph with "______" where the join goes
    # The first clause ends, then blank, then second clause starts lowercase
    prompt = (f"Which choice correctly completes the text?\n\n"
              f"{first} ______ {second[0].lower() + second[1:]}.\n\n"
              f"Which choice correctly joins the underlined clauses?")
    correct = item["correct"]
    distractors = item["wrongs"]
    expl = item.get("expl", "")
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_form_structure_sense(rng, difficulty):
    pool = FSS_PARAGRAPHS.get(difficulty) or FSS_PARAGRAPHS["easy"]
    item = rng.choice(pool)
    # The item has a paragraph with a blank, correct answer, and distractors
    prompt = (f"{item['text']}\n\nWhich choice completes the text so that it "
              f"conforms to the conventions of Standard English?")
    correct = item["correct"]
    distractors = item["wrongs"]
    expl = item["expl"]
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_transitions(rng, difficulty):
    pool = TRANSITION_PARAGRAPHS.get(difficulty) or TRANSITION_PARAGRAPHS["easy"]
    item = rng.choice(pool)
    before = item["before"]
    first = item["first"]
    second = item["second"]
    after = item.get("after", "")
    correct = item["correct"]
    distractors = item["wrongs"]
    second_lower = second[0].lower() + second[1:]
    prompt = (f"{before} {first}; ______, {second_lower}. {after}\n\n"
              f"Which transition best completes the text?")
    expl = (f"The text shows a logical relationship, so a transition such as "
            f"'{correct}' is required; the other options signal different "
            f"relationships.")
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_rhetorical_synthesis(rng, difficulty):
    fact = rng.choice(SYNTHESIS_FACTS)
    notes = (f"\u2022 Company: {fact['subject']}\n"
             f"\u2022 Founded: {fact['year1']}\n"
             f"\u2022 First product: {fact['product']}\n"
             f"\u2022 Award won: {fact['award']} in {fact['year2']}")
    if difficulty == "easy":
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
        expl = ("The goal requires foregrounding the award; only the selected option "
                "leads with it while keeping the other note facts accurate.")
    elif difficulty == "medium":
        goal = "emphasize how long ago the company was founded"
        correct = (f"Founded in {fact['year1']}, {fact['subject']} introduced the "
                   f"{fact['product']} and went on to win the {fact['award']} in "
                   f"{fact['year2']}.")
        distractors = [
            f"{fact['subject']} won the {fact['award']} in {fact['year2']} for the "
            f"{fact['product']}.",
            f"The {fact['product']} introduced by {fact['subject']} earned the "
            f"{fact['award']} in {fact['year2']}.",
            f"The {fact['award']} won by {fact['subject']} in {fact['year2']} "
            f"recognized the {fact['product']}.",
        ]
        expl = ("The goal requires leading with the founding year; the other options "
                "are factually consistent with the notes but foreground the award or "
                "product instead of the company's age.")
    else:
        goal = ("present the company's recognition as surprising given how recently "
                "it was founded")
        correct = (f"Though {fact['subject']} was founded only in {fact['year1']}, by "
                   f"{fact['year2']} its {fact['product']} had earned the "
                   f"{fact['award']}.")
        distractors = [
            f"{fact['subject']} was founded in {fact['year1']}, and in {fact['year2']} "
            f"it won the {fact['award']} for its {fact['product']}.",
            f"The {fact['award']} went to {fact['subject']} in {fact['year2']}; the "
            f"company was founded in {fact['year1']}.",
            f"{fact['subject']} introduced the {fact['product']} after {fact['year1']} "
            f"and won the {fact['award']} in {fact['year2']}.",
        ]
        expl = ("The goal requires framing the award as surprising relative to the "
                "recent founding; only the selected option sets up that contrast "
                "with 'though', while the other options list the facts neutrally.")
    prompt = (f"While researching a topic, a student has taken the following notes:\n"
              f"{notes}\n\nThe student wants to {goal}. Which choice most effectively "
              f"uses information from the notes to accomplish this goal?")
    choices, idx = build_choices(rng, correct, distractors)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


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
