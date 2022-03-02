$(() => {
    let imgTag = $("#unit_tag_img")
    let inputBox = $("#input-guess")

    // The site first needs to find out the player's timezone, to know what tag to show
    // It accepts only a timezone and not time, to prevent players from scraping the complete list
    // The server will find the player's date with UTC time and the received offset, then return the tag's path to image
    let offset = new Date().getTimezoneOffset()
    $.post({
        url: '/tzahle/offset', data: offset.toString(), contentType: 'text/plain;charset=UTF-8', success: (data) => {
            imgTag.attr("src", data)
        }
    })

    function backspaceInput() {
        let text = inputBox.val()
        inputBox.val(text.substring(0, text.length - 1))
    }

    function appendToInput(toAppend) {
        inputBox.val(inputBox.val() + toAppend)
    }

    $(".key").on("click", (event) => {
        let classes = event.target.classList
        if (classes.contains("backspace-key")) {
            backspaceInput()
        } else if (classes.contains("submit-key")) {
            // Do something
        } else {
            let toAppend = event.target.hasAttribute("data-append") ? event.target.getAttribute("data-append") : event.target.textContent
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