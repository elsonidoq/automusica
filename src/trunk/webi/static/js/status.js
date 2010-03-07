var EStatus = function EStatus(elem) {
    this.elem= elem;
    this.queue= new Array();
    this.doing_something= false;
}
EStatus.prototype.show_status= function(text, on_queue) {
    //console.log('show_status ' + this.doing_something);
    if (this.doing_something && !on_queue) {
        this.queue.push(text);
        return;
    }
    this.doing_something= true;
    var the_this= this;
    if (this.elem.is(':visible')) {
        this.elem.fadeOut(250,callback=function() {
            the_this.elem.text(text);
            the_this.elem.fadeIn(250);
            the_this.set_doing()});
    } else {
        this.elem.text(text);
        this.elem.fadeIn(500,callback=function() {the_this.set_doing()});
    }

}

EStatus.prototype.hide_status= function(on_queue) {
    if (this.doing_something && !on_queue) {
        this.queue.push(null);
        return;
    }
    this.doing_something= true;

    the_this= this;
    this.elem.fadeOut(500, callback=function() {the_this.set_doing()});
}


EStatus.prototype.set_doing= function() {
    this.doing_something= (this.queue.length > 0);
    if (this.queue.length > 0) {
        var text= this.queue.splice(0,1)[0];
        if (text) {
            this.show_status(text, on_queue=true);
        } else {
            this.hide_status(on_queue=true);
        }
    }
}

