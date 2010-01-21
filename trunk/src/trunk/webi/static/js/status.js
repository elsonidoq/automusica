var Status= function(elem) {
    this.elem= elem;
    this.queue= new Array();
    this.doing_something= false;
    this.can_clear_queue= true;
}
Status.prototype.show_status= function(text) {
    console.log('show_status ' + text);
    //console.log('show_status ' + this.doing_something);
    if (this.doing_something) {
        this.queue.push(text);
        return;
    }
    this.doing_something= true;
    if (this.elem.is(":visible")) {
        var the_elem= this.elem;
        var the_this= this;
        this.elem.fadeOut(100, function() {
            the_elem.text(text);
            the_elem.fadeIn(100);
            the_this.set_doing();
        });
    } else {
        this.elem.text(text);
        var the_this= this;
        this.elem.slideDown(callback=function() {the_this.set_doing()});
    }
}

Status.prototype.hide_status= function() {
    console.log('hide_status ');
    //console.log('hide_status ' + this.doing_something);
    if (this.doing_something) {
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
        var text= this.queue.pop();
        console.log('Queue ' + text);
        if (text) {
            this.show_status(text);
        } else {
            this.hide_status();
        }
    }
}

