import streamlit as st
from app_theme import apply_theme

NEPAL_POLICIES = [
    {
        "title": "National Parks and Wildlife Conservation Act, 2029 (1973)",
        "summary": (
            "Nepal's core wildlife law. It establishes national parks, wildlife "
            "reserves, strict nature reserves, hunting reserves, conservation "
            "areas, and buffer zones, and gives full legal protection to a "
            "named list of endangered mammals, birds, and reptiles (species "
            "such as the Bengal tiger, one-horned rhinoceros, and Asian "
            "elephant are protected under it). It criminalizes hunting and "
            "poaching of protected species and sets out enforcement powers "
            "for park and forest officers."
        ),
        "source": "https://dnpwc.gov.np/en/",
    },
    {
        "title": "Aquatic Animals Protection Act (1961)",
        "summary": (
            "An early conservation law regulating fishing methods and "
            "protecting aquatic species, predating the 1973 Act."
        ),
        "source": None,
    },
    {
        "title": "Forest Act (1993) & Forest Policy (2015)",
        "summary": (
            "Governs management of Nepal's forests, including community "
            "forestry. The 2015 policy update emphasizes sustainable forest "
            "management, reforestation, and protecting biodiversity and "
            "critical habitat within forest ecosystems."
        ),
        "source": None,
    },
    {
        "title": "Soil Conservation Act (1982)",
        "summary": (
            "Addresses watershed and soil conservation, which indirectly "
            "supports habitat protection in fragile mountain ecosystems."
        ),
        "source": None,
    },
    {
        "title": "King Mahendra Trust for Nature Conservation (1982)",
        "summary": (
            "Established Nepal's leading national conservation NGO (now the "
            "National Trust for Nature Conservation), which runs species and "
            "habitat programs alongside the government."
        ),
        "source": None,
    },
    {
        "title": "2024 protected-area infrastructure amendment",
        "summary": (
            "A January 2024 regulatory change that allows certain large "
            "infrastructure projects — hydropower dams, hotels, and tourist "
            "resorts — to be built inside national parks and protected "
            "areas. It is part of an effort to consolidate Nepal's dozen "
            "separate regulations under the 1973 Act into a single "
            "umbrella regulation. Conservation groups have raised concerns "
            "that it could threaten habitat for species such as the red "
            "panda."
        ),
        "source": "https://dialogue.earth/en/nature/can-nepals-new-wildlife-rules-balance-development-and-conservation/",
    },
]

INTERNATIONAL_POLICIES = [
    {
        "title": "CITES — Convention on International Trade in Endangered Species (1973)",
        "summary": (
            "Regulates and monitors international trade in wildlife through "
            "an appendix system: Appendix I bans commercial trade in "
            "species threatened with extinction, Appendix II requires trade "
            "permits to prevent unsustainable exploitation, and Appendix III "
            "lists species a country protects domestically and asks other "
            "parties to help control. Nepal has been a signatory since 1975."
        ),
        "source": "https://cites.org/",
    },
    {
        "title": "IUCN Red List of Threatened Species",
        "summary": (
            "Not a binding treaty, but the global reference standard for "
            "extinction risk. Species are ranked from Least Concern through "
            "Near Threatened, Vulnerable, Endangered, Critically "
            "Endangered, to Extinct, based on population trend, range, and "
            "threats — this is the classification most conservation apps "
            "and this tracker draw their status labels from."
        ),
        "source": "https://www.iucnredlist.org/",
    },
    {
        "title": "Convention on Biological Diversity (CBD, 1992)",
        "summary": (
            "A UN treaty with three goals: conserving biodiversity, using "
            "its components sustainably, and sharing the benefits of "
            "genetic resources fairly. Signatory countries commit to "
            "national biodiversity strategies and periodic targets — most "
            "recently the 2022 Kunming-Montreal Global Biodiversity "
            "Framework, which set a target of protecting 30% of land and "
            "sea globally by 2030."
        ),
        "source": "https://www.cbd.int/",
    },
    {
        "title": "Convention on Migratory Species (CMS, 1979 / Bonn Convention)",
        "summary": (
            "Protects animals that cross national borders during migration "
            "— birds, whales, sea turtles, and more — by coordinating "
            "conservation across the countries in their range."
        ),
        "source": "https://www.cms.int/",
    },
    {
        "title": "Ramsar Convention on Wetlands (1971)",
        "summary": (
            "Commits countries to conserving wetlands of international "
            "importance, which are critical habitat for many endangered "
            "aquatic and migratory species. Nepal has designated several "
            "Ramsar sites."
        ),
        "source": "https://www.ramsar.org/",
    },
    {
        "title": "World Heritage Convention (1972)",
        "summary": (
            "Protects sites of outstanding natural or cultural value, "
            "including many key wildlife habitats. Nepal's Chitwan National "
            "Park and Sagarmatha National Park are both natural World "
            "Heritage Sites."
        ),
        "source": "https://whc.unesco.org/",
    },
]


def _render_policy_list(policies, empty_message="No policies to show."):
    if not policies:
        st.caption(empty_message)
        return
    for policy in policies:
        with st.expander(policy["title"]):
            st.write(policy["summary"])
            if policy.get("source"):
                st.caption(f"More info: {policy['source']}")


def render():
    apply_theme("policies")

    st.title("Conservation Policies", anchor=False)
    st.caption(
        "A reference guide to the laws and international agreements that "
        "protect endangered species — in Nepal and globally."
    )

    tab_nepal, tab_intl = st.tabs(["🇳🇵 Nepal", "🌍 International"])

    with tab_nepal:
        st.subheader("Nepal's national policies", anchor=False)
        _render_policy_list(NEPAL_POLICIES)

    with tab_intl:
        st.subheader("International agreements", anchor=False)
        _render_policy_list(INTERNATIONAL_POLICIES)

    st.divider()
    st.caption(
        "This page is a general reference and is not a substitute for the "
        "official text of these laws and treaties."
    )