from personas.spec import PersonaSpec
from personas import (
    goal_router,
    goal_setter,
    governor,
    prompt_builder,
    schema_critic,
    schema_proposer,
    tutor,
)
from personas import extractor  # keep separate to avoid circular import formatting


def render_messages(spec: PersonaSpec, bundle, state):
    return [
        {"role": "system", "content": spec.system_prompt},
        {"role": "user", "content": spec.build_user(bundle, state)},
    ]


def schema_proposer_styles() -> list[str]:
    return list(schema_proposer.SYSTEM_PROMPTS.keys())


def schema_critic_styles() -> list[str]:
    return list(schema_critic.SYSTEM_PROMPTS.keys())


goal_setter_spec = PersonaSpec(
    name="goal_setter",
    system_prompt=goal_setter.SYSTEM_PROMPT,
    build_user=lambda bundle, state: goal_setter.build_user_message(bundle),
)


def goal_router_spec(goals):
    return PersonaSpec(
        name="goal_router",
        system_prompt=goal_router.SYSTEM_PROMPT,
        build_user=lambda bundle, state: goal_router.build_user_message(bundle, goals),
    )


def schema_proposer_spec(style: str, goal: dict) -> PersonaSpec:
    return PersonaSpec(
        name=f"schema_proposer_{style}",
        system_prompt=schema_proposer.SYSTEM_PROMPTS[style],
        build_user=lambda bundle, state: schema_proposer.build_user_message(goal, bundle),
    )


def prompt_builder_spec(goal: dict, schema, include_provenance: bool = False) -> PersonaSpec:
    return PersonaSpec(
        name="prompt_builder",
        system_prompt=prompt_builder.SYSTEM_PROMPT,
        build_user=lambda bundle, state: prompt_builder.build_user_message(goal, schema, include_provenance),
    )


def extractor_spec(prompt_text: str) -> PersonaSpec:
    return PersonaSpec(
        name="extractor",
        system_prompt=prompt_text,
        build_user=lambda bundle, state: extractor.build_user_message(bundle),
    )


def schema_critic_spec(style: str, goal: dict, schema, extraction_json: str) -> PersonaSpec:
    return PersonaSpec(
        name=f"schema_critic_{style}",
        system_prompt=schema_critic.SYSTEM_PROMPTS[style],
        build_user=lambda bundle, state: schema_critic.build_user_message(goal, schema, extraction_json, bundle),
    )


def tutor_spec(goal_json: str, schema_json: str, extraction_json: str, council_json: str) -> PersonaSpec:
    return PersonaSpec(
        name="tutor",
        system_prompt=tutor.SYSTEM_PROMPT,
        build_user=lambda bundle, state: tutor.build_user_message(goal_json, schema_json, extraction_json, council_json),
    )


def governor_spec(goal: dict, candidates) -> PersonaSpec:
    return PersonaSpec(
        name="governor",
        system_prompt=governor.SYSTEM_PROMPT,
        build_user=lambda bundle, state: governor.build_user_message(goal, candidates, bundle),
    )
