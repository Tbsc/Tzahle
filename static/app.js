$(function() {
    $(".unit_tag_img").click(function(event) {
        let url = new URL(window.location.href)
        let params = url.searchParams
        let q = params.get("q")
        if (q !== null && q !== "") {
            q += '-'
        }
        q += event.target.id
        params.set("q", q)
        window.location.href = url.href
    })
})