int val[2] = {0, 0};

function input() {
    read val[0];
    read val[1];
}

function findMax() {
    int mx = val[0];
    if(val[0] < val[1]) {
        mx = val[1];
    }
    return mx;
}

main() {
    call input();
    write call findMax();
}