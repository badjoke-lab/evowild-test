/* Race loop — movement, hurdle detection, jumping, countdown. */

var JUMP_MS = 650;
var JUMP_TRIGGER_DISTANCE = 4; /* % before hurdle when jump animation starts */
var TRACK_START_PCT = 4;       /* matches --track-start */
var TRACK_END_PCT = 96;        /* matches --track-end */

function startGame() {
    if (raceInProgress) return;

    /* Validate selection */
    var selected = document.querySelector('input[name="bet"]:checked');
    if (!selected) {
        flashError("Please select a horse first");
        return;
    }
    horseNumber = parseInt(selected.value, 10);

    bet = parseFloat(document.getElementById("money").value);
    if (isNaN(bet) || bet <= 0) {
        flashError("Enter a valid bet amount");
        return;
    }
    if (bet > coins) {
        flashError("Not enough coins — you have " + coins);
        return;
    }

    buttonClick = 1;
    document.getElementById("play").disabled = true;
    document.getElementById("resetInput").disabled = true;
    setBetControlsLocked(true);

    /* Fresh race setup */
    horsePositions = [0, 0, 0, 0, 0];
    horseSpeeds = horseSpeeds.map(function () {
        return 0.09 + Math.random() * 0.08; /* % per frame, ~0.09–0.17 */
    });

    placeHurdles();
    resetHorsePositions();
    setRaceStatus("Get ready...");

    runCountdown(function () {
        raceInProgress = true;
        setRaceStatus("Racing!");
        startLoop();
    });
}

function runCountdown(done) {
    var steps = ["3", "2", "1", "GO!"];
    countdownOverlay.classList.remove("hidden");
    var i = 0;
    function tick() {
        if (i >= steps.length) {
            countdownOverlay.classList.add("hidden");
            done();
            return;
        }
        countdownText.textContent = steps[i];
        /* restart animation */
        countdownText.classList.remove("countdown-number");
        void countdownText.offsetWidth;
        countdownText.classList.add("countdown-number");
        i++;
        setTimeout(tick, 900);
    }
    tick();
}

function resetHorsePositions() {
    for (var i = 0; i < LANE_COUNT; i++) {
        horseWrappers[i].style.transform = "translate3d(0, -50%, 0)";
        horseBodies[i].classList.remove("jumping", "winner");
        horseBodies[i].classList.remove("idle");
        horseBodies[i].classList.add("galloping");
    }
}

function startLoop() {
    var winnerLane = -1;
    var finishedAt = 0;

    function frame() {
        if (!raceInProgress) return;

        for (var i = 0; i < LANE_COUNT; i++) {
            if (horsePositions[i] >= 100) continue;

            /* Jitter speed a little each frame for unpredictability */
            var jitter = (Math.random() - 0.4) * 0.05;
            horsePositions[i] = Math.min(100, horsePositions[i] + horseSpeeds[i] + jitter);

            /* Translate horse along track using the lane's pixel width */
            var lane = horseWrappers[i].parentElement;
            var laneWidth = lane.clientWidth;
            var startPx = laneWidth * (TRACK_START_PCT / 100);
            var endPx   = laneWidth * (TRACK_END_PCT   / 100);
            var travel  = (endPx - startPx) * (horsePositions[i] / 100);
            horseWrappers[i].style.transform = "translate3d(" + travel + "px, -50%, 0)";

            maybeJump(i);

            if (horsePositions[i] >= 100 && winnerLane === -1) {
                winnerLane = i + 1;
                finishedAt = performance.now();
                triggerFinishLine();
            }
        }

        /* End race shortly after the first crosses so others catch up visually */
        if (winnerLane !== -1 && performance.now() - finishedAt > 600) {
            raceInProgress = false;
            checkWinner(winnerLane);
            return;
        }

        requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);
}

function maybeJump(i) {
    var schedule = hurdleSchedules[i];
    for (var h = 0; h < schedule.length; h++) {
        var hurdle = schedule[h];
        if (hurdle.cleared) continue;
        var distance = hurdle.pos - horsePositions[i];
        if (distance <= JUMP_TRIGGER_DISTANCE && distance > -2) {
            hurdle.cleared = true;
            triggerJump(i);
            return;
        }
    }
}

function triggerJump(i) {
    var body = horseBodies[i];
    body.classList.remove("galloping");
    body.classList.add("jumping");
    setTimeout(function () {
        body.classList.remove("jumping");
        if (raceInProgress && horsePositions[i] < 100) {
            body.classList.add("galloping");
        }
    }, JUMP_MS);
}

function triggerFinishLine() {
    var line = document.querySelector(".finish-line");
    if (!line) return;
    line.classList.remove("triggered");
    void line.offsetWidth;
    line.classList.add("triggered");
}

function setRaceStatus(text) {
    var el = document.getElementById("raceStatus");
    if (el) el.textContent = text;
}

function flashError(msg) {
    var input = document.getElementById("money");
    input.classList.add("ring-2", "ring-rose-500");
    setRaceStatus(msg);
    setTimeout(function () {
        input.classList.remove("ring-2", "ring-rose-500");
    }, 1200);
}
