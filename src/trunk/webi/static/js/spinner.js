var Spinner = function (holderid, R1, R2, count, stroke_width, on_color, off_color) {
    this.sectorsCount = count || 12,
    this.on_color = on_color || "#fff",
    this.off_color = off_color || "#fff",
    this.width = stroke_width || 15,
    this.r1 = Math.min(R1, R2) || 35,
    this.r2 = Math.max(R1, R2) || 60,
    this.r = Raphael(holderid, this.r2 * 2 + this.width * 2, this.r2 * 2 + this.width * 2),
    cx = this.r2 + this.width,
    cy = this.r2 + this.width,
    
    this.sectors = [],
    this.actual_sector=0;
    beta = 2 * Math.PI / this.sectorsCount,

    pathParams = {stroke: this.off_color, "stroke-width": this.width, "stroke-linecap": "round", opacity:0.8};
    Raphael.getColor.reset();
    for (var i = 0; i < this.sectorsCount; i++) {
        var alpha = beta * i - Math.PI / 2,
            cos = Math.cos(alpha),
            sin = Math.sin(alpha);
        this.sectors[i] = this.r.path([["M", cx + this.r1 * cos, cy + this.r1 * sin], ["L", cx + this.r2 * cos, cy + this.r2 * sin]]).attr(pathParams);
        if (this.on_color == "rainbow") {
            this.sectors[i].attr("stroke", Raphael.getColor());
        }
    }
}

Spinner.prototype.next= function() {
        this.sectors[this.actual_sector].animate({stroke:this.on_color},300);
        //this.sectors[this.actual_sector].animate({opacity:0.8},300);
        this.actual_sector+=1;
//                this.r.safari();
           // tick = setTimeout(ticker, 1000 / sectorsCount);
        /*return function () {
            clearTimeout(tick);
            r.remove();
        };*/
}


