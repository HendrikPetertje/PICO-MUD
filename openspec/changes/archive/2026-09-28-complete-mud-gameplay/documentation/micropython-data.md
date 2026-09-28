---
title: "MicroPython JSON streams and SHA-256 notes"
source: "https://github.com/micropython/micropython/blob/master/docs/library/json.rst"
created: 2026-09-28
description: "Source excerpts and project-specific persistence constraints"
tags:
  - "tool-context7"
---

Reference project checked first: its messages controller stores only RAM data
and uses json.dumps for HTTP responses. It does not establish durable saves.
The archived boot change provides verified poll/buffer constraints, so only
JSON streaming and hashing APIs needed a fresh documentation lookup.

## Source excerpts

MicroPython documentation, master retrieved via Context7 on 2026-09-28;
target firmware observed previously is 1.29.0. Verify APIs on that device
during implementation rather than treating master as a version pin.

https://github.com/micropython/micropython/blob/master/docs/library/json.rst

> json.dump(obj, stream, separators=None)
>
> Serialise obj to a JSON string, writing it to the given stream.
>
> If specified, separators should be an (item_separator, key_separator) tuple.
> The default is (', ', ': '). To get the most compact JSON representation,
> you should specify (',', ':') to eliminate whitespace.

> json.load(stream)
>
> Parses the given stream, interpreting it as a JSON string and deserialising
> the data to a Python object.
>
> Raises ValueError if the data in stream is not correctly formed.

https://github.com/micropython/micropython/blob/master/docs/library/hashlib.rst

> hash.hexdigest()
>
> This method is NOT implemented. Use binascii.hexlify(hash.digest()) to
> achieve a similar effect.

https://github.com/micropython/micropython/blob/master/docs/library/binascii.rst

> binascii.hexlify(data)
>
> Convert the bytes in the data object to a hexadecimal representation.
> Returns a bytes object.

## Application notes

- Use stream load/dump, compact separators and temporary-file replacement.
  A successful rename is per-file, not a three-file transaction.
- Mail keys must be strings in JSON; convert at the model boundary.
- Hash the agreed UTF-8 salt+password and hexlify the digest; do not call
  hexdigest or add a new hashing dependency.
- Existing MicroPython discoveries: bytearray deletion is unsupported on the
  tested firmware; EWOULDBLOCK may be absent. Reuse the fixed transport pattern.
- Capture free heap after import, after seed, after representative world growth,
  and around a save. Earlier bootstrap baseline: 431200 bytes, not a game budget.
- No LLM_WIKI_PATH was exported for this lookup; source excerpts stay here.

## Verified during implementation (2026-09-28)

MicroPython 1.29.0 on the connected Pico 2 W successfully ran streamed JSON
load/dump with compact separators, same-directory replacement, SHA-256 digest
and hexlify, and integer/string mailbox conversion. Disposable-data checks
confirmed clean saves do not rewrite, failed writes retain dirty state and
other files can still save, retries succeed, and corrupt/partial files are
preserved on refused startup. Temporary test worlds were removed afterwards.

With a verification harness loaded: seeded heap 367792 bytes, populated heap
335120 bytes, and a representative three-file save took 87 ms. These are
measurements for the exercised data, not worst-case capacity guarantees.
