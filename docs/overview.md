# Edgar-AI in two minutes

Edgar-AI is an **autonomous, persona-driven data-extraction pipeline**
targeted at SEC EDGAR filings.  Everything is phrased as an LLM reasoning
task – there are *no* hand-coded rules about what to extract or how.

High-level flow
---------------

```text
html → Goal-Setter → Discoverer → Schema-Synth → Prompt-Builder → Extractor
                                      ↑               ↓
                           Critic ← Tutor ← Governor ←┘
```

1. **Goal-Setter** reads raw filing text and decides *what information would a
   domain expert want from this document?*
2. **Discoverer** proposes candidate fields.
3. **Schema-Synth** consolidates those fields into a JSON Schema.
4. **Prompt-Builder** creates an extraction prompt that instructs the LLM to
   produce structured rows.
5. **Extractor** executes the prompt via the LLM Gateway and parses the
   function-call JSON back into `Row` objects.
6. **Critic → Tutor → Governor** forms a self-improvement loop that rewrites
   prompts, challenges them, chooses champions, and back-fills history – no
   humans in the loop.

Why is this interesting?
------------------------

* **Objective-first.**  Instead of hard-coding “terms of a loan”, we let the
  LLM articulate *itself* what matters for a given exhibit.
* **Self-evolving.**  As new document patterns appear the Critic will detect a
  score drop, Tutor will propose a fix, and Governor will promote it – the
  pipeline heals without code changes.
* **LLM-native abstractions.**  All communication is JSON that mirrors
  OpenAI’s chat-completions API.  Switching providers is one env-var away.

If you need more detail jump to [`architecture.md`](architecture.md).

