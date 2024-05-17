import capnp


capnp_version = capnp.version.version
print(f"capnp_version: {capnp_version}")


def from_bytes(schema, msg_bytes):
    if "1.0.0" in capnp_version:
        msg = schema.from_bytes(msg_bytes)
    elif "2.0.0" in capnp_version:
        with schema.from_bytes(msg_bytes) as msg:
            msg = msg
    else:
        raise ValueError(f"capnp_version {capnp_version} not supported")
    return msg
