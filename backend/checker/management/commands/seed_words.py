from django.core.management.base import BaseCommand

from checker.models import Word, WordTopic
from checker.teeline import decompose, decompose_to_letters

KNOWN_GROUPINGS = [
    "ABT", "ANY", "AS", "BD", "BT", "CD", "CHF", "CM", "CR", "CV",
    "DB", "DR", "FB", "FL", "FM", "FR", "FW", "HV", "IF", "IS",
    "IT", "MB", "MN", "MNY", "MR", "NO", "NV", "NW", "O", "OM",
    "ON", "OTHR", "PV", "RF", "SD", "SE", "SHE", "SM", "SN", "SO",
    "TB", "THS", "TLN", "TR/THR", "US", "VN", "WF", "WN", "WR", "WRD",
    "WS",
]

TOPICS = [
    ("Common Words", "common"),
    ("Journalism", "journalism"),
    ("Business", "business"),
    ("Legal", "legal"),
    ("Education", "education"),
    ("Medical", "medical"),
    ("Technology", "technology"),
    ("Government", "government"),
]

WORDS = {
    "common": [
        "the", "be", "to", "of", "and", "in", "that", "have", "it", "for",
        "not", "on", "with", "he", "do", "at", "but", "we", "his", "from",
        "they", "she", "or", "an", "will", "my", "all", "would", "there",
        "their", "what", "so", "up", "out", "if", "about", "who", "get",
        "which", "go", "me", "when", "can", "no", "just", "him", "know",
        "take", "people", "into", "year", "your", "good", "some", "could",
        "them", "see", "other", "than", "then", "now", "look", "only",
        "come", "its", "over", "think", "also", "back", "after", "use",
        "two", "how", "our", "work", "first", "well", "way", "even",
        "new", "want", "because", "any", "these", "give", "day", "most",
        "us", "great", "between", "need", "large", "under", "never",
        "each", "much", "begin", "those", "where", "must", "before",
        "long", "made", "world", "very", "still", "own", "say", "high",
        "last", "since", "right", "too", "does", "tell", "while", "home",
        "small", "end", "put", "hand", "found", "head", "place", "ask",
        "old", "run", "through", "why", "part", "again", "move", "many",
        "live", "off", "turn", "real", "leave", "life", "few", "stop",
        "keep", "start", "let", "begin", "show", "hear", "play", "pay",
        "city", "night", "point", "read", "best", "name", "side", "water",
        "line", "room", "late", "hard", "set", "open", "help", "walk",
        "change", "far", "fact", "money", "young", "book", "add", "food",
        "study", "land", "close", "light", "door", "sure", "whole",
        "power", "true", "able", "able to", "after", "together", "what",
        "account", "alternative", "business", "club", "company",
        "convenient", "develop", "enclose", "et cetera", "from",
        "general", "government", "immediate", "important",
        "opportunity", "permanent", "representative",
        "percent", "kilogram", "january", "february", "march",
        "april", "may", "july", "august", "september", "october",
        "november", "december", "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday",
        "metre", "metres", "centimetre", "centimetres",
        "kilometre", "kilometres", "litres",
        "already", "always", "another", "around", "away",
        "bad", "being", "below", "better", "big", "both", "bring",
        "call", "came", "car", "case", "centre", "certain",
        "children", "class", "clear", "cold", "complete", "country",
        "cut", "dark", "deal", "death", "decide", "deep", "different",
        "done", "down", "draw", "drive", "drop", "dry",
        "early", "east", "easy", "effect", "enough", "even",
        "every", "example", "expect", "eye", "face", "fall",
        "family", "fast", "feel", "field", "fight", "fill",
        "find", "fine", "fire", "five", "fly", "follow",
        "force", "form", "four", "free", "friend", "front",
        "full", "game", "girl", "god", "gone", "ground",
        "group", "grow", "half", "happen", "happy", "hold",
        "hope", "hot", "hour", "house", "idea", "important",
        "interest", "job", "kind", "known", "later",
        "lead", "learn", "less", "letter", "level", "life",
        "little", "look", "lord", "lose", "love",
        "low", "main", "make", "man", "matter", "mean",
        "might", "mind", "minute", "miss", "moment", "month",
        "more", "morning", "mother", "move", "name",
        "near", "next", "number", "order", "own",
        "paper", "pass", "past", "person", "picture", "plan",
        "position", "possible", "present", "problem", "produce",
        "program", "public", "pull", "push", "question",
        "quite", "reach", "reason", "receive", "record",
        "red", "remember", "rest", "result", "rise",
        "road", "school", "second", "seem", "sense", "serve",
        "seven", "several", "short", "sit", "six", "sleep",
        "social", "sort", "south", "speak", "special", "spend",
        "stand", "state", "step", "strong", "such", "suggest",
        "system", "ten", "thing", "third", "thought",
        "three", "today", "top", "town", "trade", "tree",
        "try", "understand", "until", "voice", "wait",
        "war", "watch", "week", "west", "white", "win",
        "wish", "without", "woman", "wonder", "word",
        "write", "wrong", "young",
    ],
    "journalism": [
        "report", "source", "quote", "press", "editor", "publish", "article",
        "deadline", "interview", "breaking", "headline", "column", "feature",
        "broadcast", "journalist", "newspaper", "magazine", "reporter",
        "correspondent", "editorial", "coverage", "exclusive", "investigation",
        "media", "opinion", "photograph", "review", "scoop", "story",
        "television", "bulletin", "caption", "circulation", "comment",
        "content", "copy", "digest", "dispatch", "edition", "feedback",
        "gazette", "journal", "layout", "manuscript", "network", "newsroom",
        "outlet", "panel", "podcast", "print", "production", "programme",
        "proof", "publication", "rating", "release", "response", "script",
        "segment", "serial", "signal", "statement", "supplement", "survey",
        "syndicate", "tabloid", "transcript", "update", "verify",
    ],
    "business": [
        "market", "profit", "invest", "budget", "contract", "manage",
        "strategy", "revenue", "client", "meeting", "project", "target",
        "growth", "finance", "company", "account", "annual", "asset",
        "balance", "bank", "board", "brand", "capital", "cash",
        "chairman", "commerce", "commission", "compete", "corporate",
        "cost", "credit", "customer", "debt", "demand", "director",
        "dividend", "economy", "employee", "enterprise", "estimate",
        "executive", "export", "firm", "forecast", "fund", "import",
        "income", "industry", "inflation", "insurance", "interest",
        "invoice", "lease", "liability", "loan", "loss", "margin",
        "merger", "negotiate", "office", "partner", "payment",
        "pension", "portfolio", "price", "product", "promotion",
        "purchase", "quarter", "receipt", "retail", "salary", "sale",
        "share", "stock", "supply", "surplus", "tax", "tender",
        "trade", "turnover", "value", "venture", "wage", "wholesale",
    ],
    "legal": [
        "court", "judge", "law", "trial", "evidence", "witness", "verdict",
        "appeal", "charge", "counsel", "defend", "guilty", "sentence",
        "statute", "justice", "advocate", "arrest", "bail", "barrister",
        "breach", "case", "clause", "client", "complaint", "comply",
        "confess", "consent", "constitution", "convict", "crime",
        "custody", "damage", "decree", "defendant", "dispute",
        "enforce", "exempt", "fine", "fraud", "hearing", "indict",
        "injunction", "innocent", "judgment", "jury", "lawsuit",
        "legal", "legislation", "liability", "licence", "litigation",
        "magistrate", "motion", "negligence", "oath", "offence",
        "opinion", "order", "pardon", "parole", "penalty", "petition",
        "plaintiff", "plea", "precedent", "probation", "proceed",
        "prosecute", "provision", "punish", "reform", "regulation",
        "remedy", "repeal", "ruling", "sanction", "settlement",
        "solicitor", "subpoena", "sue", "summons", "suspect",
        "testify", "testimony", "tribunal", "warrant",
    ],
    "education": [
        "teacher", "student", "school", "college", "university",
        "course", "degree", "diploma", "exam", "grade", "lecture",
        "lesson", "library", "professor", "pupil", "research",
        "science", "subject", "term", "test", "academic", "assess",
        "campus", "certificate", "classroom", "curriculum",
        "department", "discipline", "enrol", "faculty", "graduate",
        "homework", "instruct", "knowledge", "laboratory",
        "learning", "master", "method", "module", "objective",
        "practice", "qualification", "register", "scholar",
        "seminar", "skill", "syllabus", "thesis", "training",
        "tutor", "workshop",
    ],
    "medical": [
        "doctor", "patient", "hospital", "nurse", "medicine",
        "surgery", "treatment", "diagnosis", "symptom", "disease",
        "clinic", "health", "therapy", "prescription", "emergency",
        "ambulance", "blood", "condition", "consultant", "dental",
        "dose", "drug", "epidemic", "fracture", "infection",
        "injection", "mental", "operation", "organ", "pain",
        "pharmacy", "physical", "recovery", "referral", "relief",
        "scan", "specialist", "vaccine", "ward", "wound",
    ],
    "technology": [
        "computer", "software", "hardware", "network", "internet",
        "digital", "system", "data", "program", "server",
        "application", "browser", "cloud", "database", "device",
        "download", "email", "encrypt", "file", "firewall",
        "interface", "keyboard", "memory", "monitor", "online",
        "password", "platform", "process", "processor", "protocol",
        "router", "screen", "security", "signal", "storage",
        "stream", "update", "upload", "virtual", "wireless",
    ],
    "government": [
        "parliament", "minister", "cabinet", "council", "election",
        "vote", "policy", "debate", "opposition", "reform",
        "authority", "borough", "budget", "campaign", "candidate",
        "citizen", "civil", "coalition", "committee", "congress",
        "constitution", "delegate", "democracy", "department",
        "diplomat", "district", "federal", "foreign", "governor",
        "legislation", "local", "majority", "mayor", "member",
        "national", "office", "official", "petition", "political",
        "president", "proposal", "regulate", "republic", "secretary",
        "senate", "session", "speaker", "territory", "treaty",
    ],
}


def _difficulty(teeline_letters: str) -> str:
    length = len(teeline_letters)
    if length <= 3:
        return "beginner"
    elif length <= 5:
        return "intermediate"
    return "advanced"


def _compute_skeleton(word_text: str) -> str:
    try:
        components = decompose(word_text, known_groupings=KNOWN_GROUPINGS)
        return "-".join(c["letter"] for c in components)
    except (ValueError, KeyError, IndexError) as e:
        import logging
        logging.warning(f"Failed to decompose word '{word_text}': {e}")
        return ""


class Command(BaseCommand):
    help = "Seed the database with Teeline practice words (~1,000)"

    def handle(self, *args, **options):
        topic_objects = {}
        for name, slug in TOPICS:
            topic, _ = WordTopic.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )
            topic_objects[slug] = topic

        created_count = 0
        updated_count = 0
        seen = set()
        for topic_slug, words in WORDS.items():
            topic = topic_objects[topic_slug]
            for word_text in words:
                word_lower = word_text.lower().strip()
                if word_lower in seen:
                    continue
                seen.add(word_lower)

                teeline = decompose_to_letters(word_lower)
                skeleton = _compute_skeleton(word_lower)
                difficulty = _difficulty(teeline)

                word_obj, created = Word.objects.get_or_create(
                    text=word_lower,
                    defaults={
                        "teeline_letters": teeline,
                        "teeline_skeleton": skeleton,
                        "difficulty": difficulty,
                        "topic": topic,
                        "is_curated": False,
                    },
                )
                if created:
                    created_count += 1
                elif not word_obj.teeline_skeleton:
                    word_obj.teeline_skeleton = skeleton
                    word_obj.save(update_fields=["teeline_skeleton"])
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_count} words, updated {updated_count} skeletons "
                f"({len(seen)} unique words processed)"
            )
        )
