from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from quizhill_api.models import Category, ChoiceQuestion, Quiz

MOCK_AUDIO = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

CATEGORIES = [
    {
        "id": "przyroda",
        "title": "Przyroda",
        "description": "Rośliny, zwierzęta i krajobrazy Polski.",
        "image_url": "https://picsum.photos/seed/quizhill-cat-nature/400/280",
        "icon": "park_outlined",
    },
    {
        "id": "geografia",
        "title": "Geografia",
        "description": "Stolice, rzeki, góry i mapy świata.",
        "image_url": "https://picsum.photos/seed/quizhill-cat-geo/400/280",
        "icon": "public",
    },
    {
        "id": "historia",
        "title": "Historia",
        "description": "Wydarzenia, postaci i ważne daty.",
        "image_url": "https://picsum.photos/seed/quizhill-cat-history/400/280",
        "icon": "account_balance_outlined",
    },
    {
        "id": "kultura",
        "title": "Kultura",
        "description": "Sztuka, literatura, film i zwyczaje.",
        "image_url": "https://picsum.photos/seed/quizhill-cat-culture/400/280",
        "icon": "theater_comedy_outlined",
    },
    {
        "id": "sport",
        "title": "Sport",
        "description": "Dyscypliny, kluby i wielkie wydarzenia.",
        "image_url": "https://picsum.photos/seed/quizhill-cat-sport/400/280",
        "icon": "sports_soccer",
    },
    {
        "id": "nauka",
        "title": "Nauka",
        "description": "Biologia, fizyka i odkrycia naukowe.",
        "image_url": "https://picsum.photos/seed/quizhill-cat-science/400/280",
        "icon": "science_outlined",
    },
    {
        "id": "slask",
        "title": "Śląsk",
        "description": "Historia, gwara i miejsca regionu.",
        "image_url": "https://picsum.photos/seed/quizhill-cat-silesia/400/280",
        "icon": "location_city_outlined",
    },
]


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


QUIZZES = [
    {
        "id": "1",
        "title": "Najwyższe drzewa Polski",
        "description": "Sprawdź, czy znasz rekordzistów polskich lasów i parków.",
        "image_url": "https://picsum.photos/seed/quizhill-trees/200/200",
        "category_id": "przyroda",
        "kind": "choice",
        "created_at": _dt(2026, 9, 8),
        "popularity": 92,
        "questions": [
            ("Które drzewo jest uznawane za najwyższe w Polsce?", ["Daglezja", "Dąb Bartek", "Sosna zwyczajna", "Świerk pospolity"], 0),
            ("W jakim regionie rośnie najwięcej starych jodeł?", ["Sudety", "Karpaty", "Pojezierze Mazurskie", "Kaszuby"], 1),
            ("Dąb Bartek stoi w pobliżu:", ["Zagnańska", "Zakopanego", "Gdańska", "Białowieży"], 0),
            ("Który park chroni puszczę z najstarszymi drzewostanami?", ["Kampinoski Park Narodowy", "Białowieski Park Narodowy", "Wielkopolski Park Narodowy", "Ojcowski Park Narodowy"], 1),
            ("Jak mierzy się wysokość drzewa w terenie?", ["Tylko z satelity", "Wysokościomierzem / dalmierzem", "Wagą", "Kompasem"], 1),
            ("Które drzewo iglaste jest typowe dla Tatr?", ["Palma", "Limba", "Baobab", "Eukaliptus"], 1),
        ],
    },
    {
        "id": "2",
        "title": "Stolice Europy",
        "description": "Krótki quiz o stolicach państw europejskich.",
        "image_url": "https://picsum.photos/seed/quizhill-cities/200/200",
        "category_id": "geografia",
        "kind": "list",
        "time_seconds": 120,
        "created_at": _dt(2026, 9, 7),
        "popularity": 88,
        "list_prompt": "Wpisz stolice państw europejskich.",
        "list_answers": ["Paryż", "Berlin", "Madryt", "Rzym", "Lizbona", "Wiedeń", "Praga", "Budapeszt", "Oslo", "Sztokholm", "Helsinki", "Warszawa"],
    },
    {
        "id": "3",
        "title": "Historia Śląska",
        "description": "Pytania o region, z którego czerpie Quizhill.",
        "image_url": "https://picsum.photos/seed/quizhill-silesia/200/200",
        "category_id": "slask",
        "kind": "choice",
        "created_at": _dt(2026, 9, 6),
        "popularity": 81,
        "questions": [
            ("Stolicą Górnego Śląska potocznie nazywa się:", ["Opole", "Katowice", "Cieszyn", "Gliwice"], 1),
            ("Śląsk leży głównie nad rzeką:", ["Wisła", "Odra", "Warta", "Bug"], 1),
            ("Ile powstań śląskich było na początku XX wieku?", ["Jedno", "Dwa", "Trzy", "Pięć"], 2),
            ("Gwara śląska to przede wszystkim:", ["Język programowania", "Odmiana mowy regionu", "Styl tańca", "Herb"], 1),
            ("Które miasto słynie z kopalń i Industriady?", ["Sopot", "Zabrze", "Zakopane", "Ełk"], 1),
            ("Piastowie śląscy rządzili regionem w:", ["średniowieczu", "XXI wieku", "starożytnym Rzymie", "epoce wikingów na Islandii"], 0),
        ],
    },
    {
        "id": "4",
        "title": "Polskie rzeki",
        "description": "Od Wisły po mniejsze dopływy — rozpoznaj rzeki.",
        "image_url": "https://picsum.photos/seed/quizhill-rivers/200/200",
        "category_id": "geografia",
        "kind": "list",
        "time_seconds": 120,
        "created_at": _dt(2026, 9, 5),
        "popularity": 76,
        "list_prompt": "Wpisz nazwy polskich rzek.",
        "list_answers": ["Wisła", "Odra", "Warta", "Bug", "Narew", "San", "Noteć", "Pilica", "Wieprz", "Dunajec"],
    },
    {
        "id": "5",
        "title": "Znani Polacy",
        "description": "Nauka, sztuka, sport — kto zasłynął i czym.",
        "image_url": "https://picsum.photos/seed/quizhill-people/200/200",
        "category_id": "kultura",
        "kind": "choiceMusical",
        "created_at": _dt(2026, 9, 4),
        "popularity": 84,
        "audio_url": MOCK_AUDIO,
        "questions": [
            ("Kto skomponował „Poloneza As-dur” i wiele mazurków?", ["Chopin", "Moniuszko", "Lutosławski", "Penderecki"], 0),
            ("Maria Skłodowska-Curie dostała Nagrodę Nobla z:", ["literatury", "pokoju", "fizyki i chemii", "ekonomii"], 2),
            ("Mikołaj Kopernik jest znany z teorii:", ["płaskiej Ziemi", "heliocentrycznej", "kwantowej", "względności"], 1),
            ("Jan Matejko malował przede wszystkim:", ["komiksy", "sceny historyczne", "plakaty sportowe", "portrety kotów"], 1),
            ("Lech Wałęsa był związany z:", ["Solidarnością", "NASA", "FIFA", "Unią Lubelską jako król"], 0),
            ("Wisława Szymborska dostała Nobla za:", ["chemię", "literaturę", "pokój", "fizjologię"], 1),
        ],
    },
    {
        "id": "6",
        "title": "Przyroda Karpat",
        "description": "Rośliny, zwierzęta i szczyty południowej Polski.",
        "image_url": "https://picsum.photos/seed/quizhill-carpathians/200/200",
        "category_id": "przyroda",
        "kind": "list",
        "time_seconds": 120,
        "created_at": _dt(2026, 9, 3),
        "popularity": 71,
        "list_prompt": "Wpisz szczyty, zwierzęta albo miejsca Karpat.",
        "list_answers": ["Rysy", "Giewont", "Babia Góra", "Tarnica", "Śnieżka", "Niedźwiedź", "Ryś", "Świstak", "Tatry", "Bieszczady"],
    },
    {
        "id": "7",
        "title": "Piłka nożna — reprezentacja",
        "description": "Bramki, trenerzy i wielkie turnieje kadry.",
        "image_url": "https://picsum.photos/seed/quizhill-football/200/200",
        "category_id": "sport",
        "kind": "choice",
        "created_at": _dt(2026, 9, 2),
        "popularity": 95,
        "questions": [
            ("Reprezentacja Polski gra w:", ["biało-czerwonych barwach", "zielono-czarnych", "tylko złotych", "niebieskich"], 0),
            ("Stadion Narodowy stoi w:", ["Krakowie", "Gdańsku", "Warszawie", "Poznaniu"], 2),
            ("Robert Lewandowski to przede wszystkim:", ["bramkarz", "napastnik", "sędzia", "trener kadry w latach 50."], 1),
            ("Mistrzostwa świata organizuje:", ["FIFA", "NBA", "UEFA tylko hokej", "IOC pływanie"], 0),
            ("Orły to potocznie:", ["kadra Niemiec", "kadra Polski", "sędziowie VAR", "kibice Anglii"], 1),
            ("Euro 2012 Polska organizowała wraz z:", ["Czechami", "Ukrainą", "Słowacją", "Litwą"], 1),
        ],
    },
    {
        "id": "8",
        "title": "Układ Słoneczny",
        "description": "Planety, księżyce i odległości w kosmosie.",
        "image_url": "https://picsum.photos/seed/quizhill-space/200/200",
        "category_id": "nauka",
        "kind": "list",
        "time_seconds": 120,
        "created_at": _dt(2026, 9, 1),
        "popularity": 79,
        "list_prompt": "Wpisz planety Układu Słonecznego.",
        "list_answers": ["Merkury", "Wenus", "Ziemia", "Mars", "Jowisz", "Saturn", "Uran", "Neptun"],
    },
    {
        "id": "9",
        "title": "Zamki i pałace",
        "description": "Warownie Polski — od Malborka po Pieskową Skałę.",
        "image_url": "https://picsum.photos/seed/quizhill-castles/200/200",
        "category_id": "historia",
        "kind": "choice",
        "created_at": _dt(2026, 8, 28),
        "popularity": 67,
        "questions": [
            ("Zamek w Malborku zbudowali:", ["Krzyżacy", "Wikingowie", "Aztekowie", "Celtowie z Irlandii"], 0),
            ("Wawel znajduje się w:", ["Krakowie", "Lublinie", "Szczecinie", "Olsztynie"], 0),
            ("Zamek Książ leży koło:", ["Wałbrzycha", "Gdyni", "Zamościa", "Suwałk"], 0),
            ("Pałac w Wilanowie to rezydencja:", ["Jana III Sobieskiego", "Bolesława Chrobrego", "Kazimierza Wielkiego tylko w Gdańsku", "Mieszka I w Paryżu"], 0),
            ("Pieskowa Skała słynie z:", ["wydm", "zamku i Maczugi Herkulesa", "portu morskiego", "kopalni soli tylko"], 1),
            ("Który zamek stoi nad Dunajcem w Pieninach?", ["Niedzica", "Malbork", "Książ", "Ogrodzieniec jest nad morzem"], 0),
        ],
    },
    {
        "id": "10",
        "title": "Gwara śląska",
        "description": "Słówka, zwroty i pułapki dla godki.",
        "image_url": "https://picsum.photos/seed/quizhill-dialect/200/200",
        "category_id": "slask",
        "kind": "listMusical",
        "created_at": _dt(2026, 8, 26),
        "popularity": 73,
        "audio_url": MOCK_AUDIO,
        "list_prompt": "Wpisz śląskie słowa albo zwroty.",
        "list_answers": ["Kaj", "Joch", "Fajnie", "Bana", "Gruba", "Szolka", "Modrzejów", "Hanys", "Godka", "Krupniok"],
    },
    {
        "id": "11",
        "title": "Parki narodowe",
        "description": "Od Białowieży po Tatry — poznaj polskie parki.",
        "image_url": "https://picsum.photos/seed/quizhill-parks/200/200",
        "category_id": "przyroda",
        "kind": "choice",
        "created_at": _dt(2026, 8, 24),
        "popularity": 64,
        "questions": [
            ("Najstarszy park narodowy w Polsce to:", ["Tatrzański", "Białowieski", "Słowiński", "Pieniński"], 1),
            ("Rysy leżą w parku:", ["Karkonoskim", "Tatrzańskim", "Biebrzańskim", "Wielkopolskim"], 1),
            ("Słowiński Park Narodowy słynie z:", ["wydm", "wulkanów", "palm", "gejzerów"], 0),
            ("Puszcza Białowieska jest znana z:", ["żubrów", "pingwinów", "lwów", "krokodyli"], 0),
            ("Ojcowski Park Narodowy leży koło:", ["Krakowa", "Gdańska", "Szczecina", "Wrocławia nad morzem"], 0),
            ("Ile parków narodowych jest w Polsce (rząd wielkości)?", ["2", "ok. 23", "100", "1"], 1),
        ],
    },
    {
        "id": "12",
        "title": "Literatura polska",
        "description": "Autorzy, tytuły i cytaty z kanonu szkolnego.",
        "image_url": "https://picsum.photos/seed/quizhill-books/200/200",
        "category_id": "kultura",
        "kind": "listMusical",
        "created_at": _dt(2026, 8, 20),
        "popularity": 58,
        "audio_url": MOCK_AUDIO,
        "list_prompt": "Wpisz nazwiska polskich pisarzy albo poetów.",
        "list_answers": ["Mickiewicz", "Słowacki", "Sienkiewicz", "Prus", "Reymont", "Miłosz", "Szymborska", "Herbert", "Gombrowicz", "Lem"],
    },
    {
        "id": "13",
        "title": "Olimpijczycy",
        "description": "Medale, rekordy i dyscypliny igrzysk.",
        "image_url": "https://picsum.photos/seed/quizhill-olympics/200/200",
        "category_id": "sport",
        "kind": "list",
        "time_seconds": 120,
        "created_at": _dt(2026, 8, 18),
        "popularity": 61,
        "list_prompt": "Wpisz nazwiska polskich olimpijczyków.",
        "list_answers": ["Małysz", "Stoch", "Żyła", "Włodarczyk", "Korzeniowski", "Iwan", "Blach", "Kubacki", "Nowicki", "Kowalczyk"],
    },
    {
        "id": "14",
        "title": "Chemia w kuchni",
        "description": "Reakcje, które dzieją się przy obiedzie.",
        "image_url": "https://picsum.photos/seed/quizhill-chemistry/200/200",
        "category_id": "nauka",
        "kind": "choice",
        "created_at": _dt(2026, 8, 14),
        "popularity": 52,
        "questions": [
            ("Soda oczyszczona z octem daje przede wszystkim:", ["dwutlenek węgla", "złoto", "hel", "chlor"], 0),
            ("Smażenie to obróbka w:", ["wysokiej temperaturze tłuszczu", "próżni kosmicznej", "ciekłym azocie zawsze", "samym świetle"], 0),
            ("Drożdże w cieście wytwarzają:", ["dwutlenek węgla", "rtęć", "plastik", "żelazo"], 0),
            ("Sól kuchenna to głównie:", ["NaCl", "H2O", "CO2", "Fe2O3"], 0),
            ("Karmel powstaje przy:", ["podgrzewaniu cukru", "mrożeniu wody", "mieszaniu piasku", "świeceniu latarki"], 0),
            ("Białko jajka ścina się od:", ["ciepła", "magnesu", "ciszy", "koloru miski"], 0),
        ],
    },
    {
        "id": "15",
        "title": "Powstania śląskie",
        "description": "Daty, miejsca i skutki trzech powstań.",
        "image_url": "https://picsum.photos/seed/quizhill-uprisings/200/200",
        "category_id": "historia",
        "kind": "list",
        "time_seconds": 120,
        "created_at": _dt(2026, 8, 10),
        "popularity": 55,
        "list_prompt": "Wpisz miejsca albo daty związane z powstaniami śląskimi.",
        "list_answers": ["Katowice", "Opole", "Góra Świętej Anny", "1920", "1921", "1919", "Pszczyna", "Rybnik"],
    },
    {
        "id": "16",
        "title": "Wyspy świata",
        "description": "Oceany, stolice i rekordowe archipelagi.",
        "image_url": "https://picsum.photos/seed/quizhill-islands/200/200",
        "category_id": "geografia",
        "kind": "choice",
        "created_at": _dt(2026, 8, 6),
        "popularity": 49,
        "questions": [
            ("Największa wyspa świata to:", ["Grenlandia", "Madagaskar", "Irlandia", "Wolin"], 0),
            ("Wyspy Kanaryjskie należą do:", ["Hiszpanii", "Polski", "Kanady", "Japonii"], 0),
            ("Japonia to państwo:", ["kontynentalne bez wysp", "archipelagowe", "tylko pustynne", "śródziemnomorskie w Afryce"], 1),
            ("Islandia leży na oceanie:", ["Atlantyckim", "Indyjskim", "Spokojnym przy Chile", "Południowym przy Antarktydzie tylko"], 0),
            ("Malta to wyspa na:", ["Morzu Śródziemnym", "Bałtyku", "Morzu Czarnym", "Jeziorze Bodeńskim"], 0),
            ("Wyspy Hawajskie leżą na oceanie:", ["Spokojnym", "Atlantyckim", "Arktycznym", "Indyjskim przy Madagaskarze"], 0),
        ],
    },
]


async def seed_if_empty(db: AsyncSession) -> None:
    count = await db.scalar(select(func.count()).select_from(Category))
    if count:
        return
    await seed_catalog(db)


async def seed_catalog(db: AsyncSession) -> None:
    for item in CATEGORIES:
        db.add(Category(**item))
    await db.flush()
    for item in QUIZZES:
        questions = item.get("questions") or []
        kind = item["kind"]
        quiz = Quiz(
            id=item["id"],
            title=item["title"],
            description=item["description"],
            image_url=item.get("image_url"),
            category_id=item["category_id"],
            kind=kind,
            created_at=item["created_at"],
            popularity=item["popularity"],
            time_seconds=item.get("time_seconds", 90 if kind.startswith("list") else 6),
            audio_url=item.get("audio_url"),
            list_prompt=item.get("list_prompt"),
            list_image_url=item.get("image_url") if kind.startswith("list") else None,
            list_answers=item.get("list_answers"),
        )
        db.add(quiz)
        await db.flush()
        for index, question in enumerate(questions):
            prompt, options, correct = question
            db.add(
                ChoiceQuestion(
                    quiz_id=quiz.id,
                    prompt=prompt,
                    image_url=item.get("image_url"),
                    options=options,
                    correct_index=correct,
                    sort_order=index,
                )
            )
    await db.commit()
