import api


sequence = [[0, 0], [400, 400], [500, 400], [500, 500]]

for s in sequence:
    P_map = {
        "F1_DSP111": s[0],
        "F1_DSP112": s[1],
    }

    print(f"Set OP for {P_map}")

    PQ_map = api.set_DERs(P_map)

    print(f"Set OP for {PQ_map}")
    input(f"Press enter to continue")
