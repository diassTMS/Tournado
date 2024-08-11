// DOM utility functions:

const ELS = (sel, par) => (par || document).querySelectorAll(sel);

// TASK:

const ELS_child = ELS(".float-child");

let EL_drag; // Used to remember the dragged element

const addEvents = (EL_ev) => {
  EL_ev.setAttribute("draggable", "true");
  EL_ev.addEventListener("dragstart", onstart);
  EL_ev.addEventListener("touchstart", onstart);
  EL_ev.addEventListener("dragover", (ev) => ev.preventDefault());
  EL_ev.addEventListener("touchmove", (ev) => ev.preventDefault());
  EL_ev.addEventListener("drop", ondrop);
  EL_ev.addEventListener("touchend", ondrop);
  EL_ev.draggable({
    scroll: false,
    containment: "#card",
    
    start: function( event, ui ) {
        console.log("start top is :" + ui.position.top)
        console.log("start left is :" + ui.position.left)
    },
    drag: function(event, ui) {
        console.log('draging.....');    
    },
    stop: function( event, ui ) {
        console.log("stop top is :" + ui.position.top)
        console.log("stop left is :" + ui.position.left)
    }    
});
};

const onstart = (ev) => {
  EL_drag = ev.currentTarget;
  console.log(EL_drag);
}

const ondrop = (ev) => {
  if (!EL_drag) return;

  ev.preventDefault();
  
  const EL_targ = ev.currentTarget;
  console.log(EL_drag);
  console.log(EL_targ);
  const EL_targClone = EL_targ.cloneNode(true);
  const EL_dragClone = EL_drag.cloneNode(true);

  var targId = EL_targ.id;
  var dragId = EL_drag.id;
  console.log(targId);
  console.log(dragId);
  send_request(dragId, targId);

  //changeData(EL_drag.id, targPitch);
  //changeData(EL_targ.id, dragPitch);
  
  EL_targ.replaceWith(EL_dragClone);
  EL_drag.replaceWith(EL_targClone);
  
  addEvents(EL_targClone); // Reassign events to cloned element
  addEvents(EL_dragClone); // Reassign events to cloned element
  
  EL_drag = undefined;
};

ELS_child.forEach((EL_child) => addEvents(EL_child));

function send_request(matchOne_id, matchTwo_id){
  $.ajax({
    type: 'GET',
    url: `/task-assign/${matchOne_id}/${matchTwo_id}/`,
    failure: function(data){
      console.log('failure');
      console.log(data);
    },
  });
}