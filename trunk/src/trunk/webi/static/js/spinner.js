var Spinner = function (holderid, R1, R2, count, stroke_width, 
                        on_color, off_color, 
                        ntraining, training_on_color, training_off_color) {

    this.sectorsCount = count || 12,
    this.on_color = on_color || "#fff",
    this.off_color = off_color || "#fff",
    this.training_on_color = training_on_color || "#fff",
    this.training_off_color = training_off_color || "#fff",
    this.ntraining = ntraining || 0,
    this.width = stroke_width || 15,
    this.r1 = Math.min(R1, R2) || 35,
    this.r2 = Math.max(R1, R2) || 60,
    this.r = Raphael(holderid, this.r2 * 2 + this.width * 2, this.r2 * 2 + this.width * 2),
    cx = this.r2 + this.width,
    cy = this.r2 + this.width,
    
    this.sectors = [],
    this.actual_sector=0;
    beta = 2 * Math.PI / this.sectorsCount,

    pathParams = {"stroke-width": this.width, "stroke-linecap": "round", opacity:0.8};
    Raphael.getColor.reset();
    for (var i = 0; i < this.sectorsCount; i++) {
        var alpha = beta * i - Math.PI / 2,
            cos = Math.cos(alpha),
            sin = Math.sin(alpha);
            if( i < this.ntraining) {
                pathParams['stroke']= training_off_color;
            } else {
                pathParams['stroke']= off_color;
            }
            this.sectors[i] = this.r.path([["M", cx + this.r1 * cos, cy + this.r1 * sin], ["L", cx + this.r2 * cos, cy + this.r2 * sin]]).attr(pathParams);
    }
}

Spinner.prototype.next= function() {
        var color= null;
        if (this.in_training()) {
            color= this.training_on_color;
        } else {
            color= this.on_color;
        }
        this.sectors[this.actual_sector].animate({stroke:color},300);

        //this.sectors[this.actual_sector].animate({opacity:0.8},300);
        this.actual_sector+=1;
//                this.r.safari();
           // tick = setTimeout(ticker, 1000 / sectorsCount);
        /*return function () {
            clearTimeout(tick);
            r.remove();
        };*/
}


Spinner.prototype.in_training= function() {
    return this.actual_sector < this.ntraining;
}
