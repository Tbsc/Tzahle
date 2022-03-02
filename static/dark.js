$(() => {
    const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");
    let toggle = $("#toggle-dark")
    let darkModeStored = window.localStorage.getItem("dark-theme")

    if (darkModeStored === "true" || (darkModeStored === null && prefersDarkScheme.matches)) {
      document.body.classList.add("dark-theme");
      toggle.prop("checked", true)
    } else {
      document.body.classList.remove("dark-theme");
      toggle.prop("checked", false)
    }

    toggle.on("click", () => {
        if (document.body.classList.contains("dark-theme")) {
            document.body.classList.remove("dark-theme")
            window.localStorage.setItem("dark-theme", "false")
        } else {
            document.body.classList.add("dark-theme")
            window.localStorage.setItem("dark-theme", "true")
        }
    })
})