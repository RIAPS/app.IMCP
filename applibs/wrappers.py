import capnp


capnp_version = capnp.version.version
print(f"capnp_version: {capnp_version}")


def from_bytes(schema, msg_bytes):
    if capnp_version == "1.0.0":
        msg = schema.from_bytes(msg_bytes)
    elif capnp_version == "2.0.0":
        with schema.from_bytes(msg_bytes) as msg:
            msg = msg
    else:
        raise ValueError(f"capnp_version {capnp_version} not supported")
    return msg
