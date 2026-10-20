# Lidr.co-Master repository context

## Runner scheduling

Ordinary jobs use the existing `pinedatec` self-hosted pool, shared by
Kopernicus and Ragnarok. Do not introduce the unregistered `primary` label.
Tracking: [#6](https://github.com/PinedaTec-EU/Lidr.co-Master/issues/6).

## Shared agent routing

Use [the generated skill index](../.skills/index.md) for authored PR summaries
and strict judge validation. Compilation mode is `none`; existing
version/publication workflows are preserved. Tracking: [#9](https://github.com/PinedaTec-EU/Lidr.co-Master/issues/9).
