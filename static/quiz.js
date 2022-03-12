$(() => {
    let guessedSomething = false

    let contentType = "text/plain;charset=UTF-8"

    let guessBtn = $("#guess")
    let guessBox = $("#input-guess")
    let message = $("#guess-message")
    let answer = $("#guess-answer")
    let score = $("#score-num")
    let tagLink = $("#unit_tag_link")
    let giveup = $("#giveup")

    function setDisabled(elem, state) {
        elem.prop("disabled", state)
    }

    function displayAnswer(resp, doDisableGuessBtn = true) {
        answer.show()
        answer.text(resp["name"])
        score.text(resp["score"])
        tagLink.prop("href", resp["rel_path"])
        if (doDisableGuessBtn) {
            setDisabled(guessBtn, doDisableGuessBtn)
        }
    }

    function showMessage(msg) {
        message.show()
        message.text(msg)
    }

    function answerShown() {
        // Use the visibility of the answer div to determine if the player successfully guessed already
        return answer.css("display") !== "none"
    }

    function setAllowInputGuess(state) {
        setDisabled(guessBox, !state)
        setDisabled(guessBtn, !state)
    }

    function checkGuess() {
        // Only allow guessing as long as the answer wasn't shown
        if (!answerShown()) {
            // Block guessing again until backend responds
            setAllowInputGuess(false)
            let tooLongTimer = setTimeout(() => {
                showMessage("הבדיקה לוקחת יותר מדי זמן...")
            }, 500)
            $.post({
                url: "quiz", data: guessBox.val(), contentType: contentType, success: (data) => {
                    // This is the success callback, so 400 errors won't reach this
                    guessedSomething = true
                    if (data === "incorrect") {
                        showMessage("לא...")
                    } else {
                        showMessage("נחמד!")
                        displayAnswer(data)
                        setDisabled(giveup, true)
                    }
                }
            }).always(() => {
                clearTimeout(tooLongTimer)
                setAllowInputGuess(true)
            });
        }
    }

    guessBox.bind("keypress", (event) => {
        if (event.which === 13) {
            event.preventDefault()
            checkGuess()
        }
    })
    guessBtn.on("click", () => {
        checkGuess()
    })

    $("#next").click(() => {
        location.reload()
    })

    function showObjectionBtn() {
        guessBtn.text("הניחוש שלי נכון!")
        guessBtn.unbind('click')
        guessBtn.on("click", () => {
            $.post({
                url: "/quiz/objection", success: () => {
                    showMessage("הערעור נשלח בהצלחה!")
                    // TODO prevent objecting more than once
                }
            })
        })
    }

    giveup.click(() => {
        // Ponder upon a player guessing correctly, then pressing the show answer button only to have their
        // success nullified. That is definitely not wanted, I can assure you.
        // I mean, the effect is minimal, doing this doesn't cancel out the point earned and is quickly erased
        // when the page is reloaded, but still, it's not a good experience for the player.
        if (!answerShown()) {
            $.post({
                url: "/quiz", data: "giveup", contentType: contentType, success: (data) => {
                    showMessage("חבל...")
                    displayAnswer(data, !guessedSomething)

                    // If the player gave up AFTER guessing something, let them object to their loss
                    if (guessedSomething) {
                        showObjectionBtn()
                    }
                }
            })
        }
    })
})