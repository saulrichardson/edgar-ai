from personas.spec import PersonaSpec
from personas import goal_setter, schema_synth, prompt_builder, extractor, critic, discoverer, tutor, governor, breaker


def render_messages(spec: PersonaSpec, bundle, state):
    return [
        {"role": "system", "content": spec.system_prompt},
        {"role": "user", "content": spec.build_user(bundle, state)},
    ]


# Base specs (note: some specs are factories to close over parameters)
goal_setter_spec = PersonaSpec(
    name="goal_setter",
    system_prompt=goal_setter.SYSTEM_PROMPT,
    build_user=goal_setter.build_user_message,
)


def schema_synth_spec(goal_text: str) -> PersonaSpec:
    return PersonaSpec(
        name="schema_synth",
        system_prompt=schema_synth.SYSTEM_PROMPT,
        build_user=lambda bundle, state: schema_synth.build_user_message(goal_text, bundle),
    )


def prompt_builder_spec(variant) -> PersonaSpec:
    return PersonaSpec(
        name="prompt_builder",
        system_prompt=prompt_builder.SYSTEM_PROMPT,
        build_user=lambda bundle, state: prompt_builder.build_user_message(variant),
    )


def extractor_spec(prompt_text: str) -> PersonaSpec:
    return PersonaSpec(
        name="extractor",
        system_prompt=prompt_text,
        build_user=lambda bundle, state: extractor.build_user_message(bundle),
    )


def critic_spec(extraction_json: str) -> PersonaSpec:
    return PersonaSpec(
        name="critic",
        system_prompt=critic.SYSTEM_PROMPT,
        build_user=lambda bundle, state: critic.build_user_message(bundle, extraction_json),
    )


def discoverer_spec(goal_text: str) -> PersonaSpec:
    return PersonaSpec(
        name="discoverer",
        system_prompt=discoverer.SYSTEM_PROMPT,
        build_user=lambda bundle, state: discoverer.build_user_message(goal_text, bundle),
    )


def tutor_spec(prompt_text: str, extraction: str, critique: str) -> PersonaSpec:
    return PersonaSpec(
        name="tutor",
        system_prompt=tutor.SYSTEM_PROMPT,
        build_user=lambda bundle, state: tutor.build_user_message(prompt_text, extraction, critique),
    )


def governor_spec(champion_score: int, challenger_score: int, champion_crit: str, challenger_crit: str) -> PersonaSpec:
    return PersonaSpec(
        name="governor",
        system_prompt=governor.SYSTEM_PROMPT,
        build_user=lambda bundle, state: governor.build_user_message(champion_score, challenger_score, champion_crit, challenger_crit),
    )


def breaker_spec(goal_text: str, prompt_text: str) -> PersonaSpec:
    return PersonaSpec(
        name="breaker",
        system_prompt=breaker.SYSTEM_PROMPT,
        build_user=lambda bundle, state: breaker.build_user_message(goal_text, prompt_text),
    )
