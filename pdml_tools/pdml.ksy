meta:
  id: pdml
  title: FloTHERM PDML
  application: Simcenter FloTHERM
  file-extension:
    - pdml
  endian: be
  ks-version: 0.10
doc: |
  Initial Kaitai Struct description for FloTHERM PDML.

  The format is only partially understood today, so the top-level parser keeps the
  payload opaque and defines trusted sub-structures that can be reused while the
  schema grows:
  - header line
  - tagged UTF-8 strings (07 02 ...)
  - tagged doubles (06 + IEEE754 double)

  In practice, use this schema together with the Python scanner in
  `pdml_tools/pdml_construct_schema.py`:
  - Kaitai holds the canonical field layout for confirmed record types
  - Python performs marker scanning until more of the stream framing is known

seq:
  - id: header
    type: header_line
  - id: payload
    size-eos: true

types:
  header_line:
    doc: ASCII header line terminated by LF. Example: "PDML 2504 Simcenter Flotherm 2504"
    seq:
      - id: raw
        type: str
        terminator: 10
        include-terminator: false
        encoding: ASCII

  tagged_string:
    doc: |
      Confirmed string record layout:
      07 02 [type_code: u2be] [reserved: u2be] [byte_length: u4be] [utf8 bytes]
    seq:
      - id: marker
        contents:
          - 0x07
          - 0x02
      - id: type_code
        type: u2
      - id: reserved
        type: u2
      - id: byte_length
        type: u4
      - id: value
        type: str
        size: byte_length
        encoding: UTF-8

  tagged_double:
    doc: Confirmed tagged big-endian IEEE754 double: 06 [8-byte double]
    seq:
      - id: marker
        contents:
          - 0x06
      - id: value
        type: f8

  geometry_name_record:
    doc: |
      Alias for tagged_string when the type_code corresponds to a geometry object.
      Current confirmed geometry type codes include 0x0250 cuboid, 0x0280 prism,
      0x0320 fan, 0x0340 heatsink, 0x0350 pcb, 0x0740 network_assembly, etc.
    seq:
      - id: base
        type: tagged_string
