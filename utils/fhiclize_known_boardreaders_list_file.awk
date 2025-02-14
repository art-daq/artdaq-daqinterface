
{

    if ($0 ~ /^\s*#/ ) {
	next
    }

    if ($0 ~ /^\s*$/ ) {
	next
    }

    part_of_string=0

    printf("%s: [", $1);
    for (i = 2; i <= NF; ++i) {
        if ($i ~ /^"/) {
           part_of_string=1
	}

        if (part_of_string != 1) {
	    printf("\"%s\"", $i);

	    if (i != NF) {
		printf(", ");
	    } else {
		printf("]\n");
	    }
	} else {
	    printf("%s ", $i);

            if (i == NF) {
		printf("]\n");
	    }
	}

        if ($i ~ /"$/) {
            part_of_string=0
	}
    }
}
