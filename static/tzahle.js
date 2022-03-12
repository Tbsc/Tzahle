$(() => {
    let imgTag = $("#unit_tag_img")

    // The site first needs to find out the player's timezone, to know what tag to show
    // It accepts only a timezone and not time, to prevent players from scraping the complete list
    // The server will find the player's date with UTC time and the received offset, then return the tag's path to image
    let offset = new Date().getTimezoneOffset()
    $.post({
        url: '/tzahle/offset', data: offset.toString(), contentType: 'text/plain;charset=UTF-8', success: (data) => {
            imgTag.attr("src", data)
        }
    })

    // // Build input boxes in DOM
    // for (let i = 0; i < 6; i++) {
    //     let baseDiv = document.createElement("div")
    //     baseDiv.id = "input-box-" + i.toString()
    //     baseDiv.classList.add("input-box")
    //     if (i === 0) {
    //         baseDiv.classList.add("input-box-active")
    //     }
    //     let content = document.createElement("span")
    //     content.classList.add("input-box-content")
    //     baseDiv.appendChild(content)
    //     document.getElementById("input-boxes-container").appendChild(baseDiv)
    // }

    // Doesn't know how to handle guesses made in previous load of page yet
    $("#input-box-0").addClass("input-box-active")

    let guessesMarkedWords = []

    function activeInputBox() {
        return $(".input-box.input-box-active")
    }

    function activeInputContent() {
        return $(".input-box.input-box-active > .input-box-content")
    }

    function setActiveInputContent(content) {
        activeInputContent().text(content)
    }

    function getActiveInputContent() {
        return activeInputContent().text()
    }

    function switchToInputBox(newBoxNum) {
        let cur = activeInputBox()
        let next = $("#input-box-" + parseInt(newBoxNum))
        cur.removeClass("input-box-active")
        if (next.length) {
            next.addClass("input-box-active")
        }
    }

    function moveToNextInputBox() {
        switchToInputBox(parseInt(activeInputBox().attr("id").split("-")[2]) + 1)
    }

    function successSequence() {
        activeInputContent().addClass("input-green-highlight")
        switchToInputBox(99) // No box
        $("#success-dialog").css("display", "flex")
        $("#control-copy-result").click(() => {
            let str = 'צָהֶ"ל '
            str += guessesMarkedWords.length
            str += '/6\n\n'
            for (let guess of guessesMarkedWords) {
                let lastWordIdx = guess[guess.length - 1]
                for (let i = 0; i <= lastWordIdx; i++) {
                    if (i in guess) {
                        str += "🟩"
                    } else {
                        str += "⬜"
                    }
                }
                str += '\n'
            }
            str += 'q.tbsc.dev/tzahle'
            navigator.clipboard.writeText(str)
        })
    }

    function backspaceInput() {
        let text = getActiveInputContent()
        setActiveInputContent(text.substring(0, text.length - 1))
    }

    function appendToInput(toAppend) {
        setActiveInputContent(getActiveInputContent() + toAppend)
    }

    jQuery.fn.highlight = function (str, className) {
        let regex = new RegExp(str, "gi");

        return this.each(function () {
            this.innerHTML = this.innerHTML.replace(regex, function(matched) {return "<span class=\"" + className + "\">" + matched + "</span>";});
        });
    };

    function submitGuess() {
        if (activeInputBox()) {
            $.post({
                url: "/tzahle",
                data: getActiveInputContent(),
                contentType: 'text/plain;charset=UTF-8',
                success: (data) => {
                    if (data["resp_type"] === "hint") {
                        activeInputContent().addClass("input-red-highlight")
                        let wordIdxs = data["word_indices"]
                        let toSave = []
                        for (let i of wordIdxs) {
                            let word = activeInputContent().text().split(/\s+/)[parseInt(i)]
                            activeInputContent().highlight(word, "input-green-highlight")
                            toSave += parseInt(i)
                        }
                        guessesMarkedWords += toSave
                        moveToNextInputBox()
                    } else if (data["resp_type"] === "answer") {
                        successSequence()
                    }
                }
            })
        }
    }

    $(".key").on("click", (event) => {
        let classes = event.target.classList
        if (classes.contains("backspace-key")) {
            backspaceInput()
        } else if (classes.contains("submit-key")) {
            submitGuess()
        } else {
            let toAppend = event.target.getAttribute("data-append") ?? event.target.textContent
            appendToInput(toAppend)
        }
    })

    let keyConv = {
        "KeyP": "פ",
        "KeyO": "ם",
        "KeyI": "ן",
        "KeyU": "ו",
        "KeyY": "ט",
        "KeyT": "א",
        "KeyR": "ר",
        "KeyE": "ק",
        "Quote": '"',
        "Semicolon": "ף",
        "KeyL": "ך",
        "KeyK": "ל",
        "KeyJ": "ח",
        "KeyH": "י",
        "KeyG": "ע",
        "KeyF": "כ",
        "KeyD": "ג",
        "KeyS": "ד",
        "KeyA": "ש",
        "Period": "ץ",
        "Comma": "ת",
        "KeyM": "צ",
        "KeyN": "מ",
        "KeyB": "נ",
        "KeyV": "ה",
        "KeyC": "ב",
        "KeyX": "ס",
        "KeyZ": "ז",
        "Digit0": "0",
        "Digit1": "1",
        "Digit2": "2",
        "Digit3": "3",
        "Digit4": "4",
        "Digit5": "5",
        "Digit6": "6",
        "Digit7": "7",
        "Digit8": "8",
        "Digit9": "9",
        "Space": " "
    }

    $("body").bind("keydown", (event) => {
        if (event.code === "Enter") {
            submitGuess()
        } else if (event.code === "Backspace") {
            backspaceInput()
        } else if (keyConv[event.code] !== undefined) {
            if (event.code === "Quote") {
                event.preventDefault()
            }
            appendToInput(keyConv[event.code])
        }
    })
})