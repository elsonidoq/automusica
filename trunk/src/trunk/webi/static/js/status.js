var Status= function(elem) {
    this.elem= elem;
    this.queue= new Array();
    this.doing_something= false;
}
Status.prototype.show_status= function(text, on_queue) {
    //console.log('show_status ' + this.doing_something);
    if (this.doing_something && !on_queue) {
        this.queue.push(text);
        return;
    }
    this.doing_something= true;
    this.elem.text(text);

    var the_this= this;
    this.elem.slideDown(500,callback=function() {the_this.set_doing()});
}

Status.prototype.hide_status= function(on_queue) {
    if (this.doing_something && !on_queue) {
        this.queue.push(null);
        return;
    }
    this.doing_something= true;

    the_this= this;
    this.elem.slideUp(callback=function() {the_this.set_doing()});
}


Status.prototype.set_doing= function() {
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

