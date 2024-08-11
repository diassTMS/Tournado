// DOM utility functions:

const ELS = (sel, par) => (par || document).querySelectorAll(sel);


// TASK:

const ELS_child = ELS(".float-child");

let EL_drag; // Used to remember the dragged element

const addEvents = (EL_ev) => {
  console.log('hi')
  EL_ev.setAttribute("draggable", "true");
  EL_ev.addEventListener("dragstart", onstart);
  EL_ev.addEventListener("dragover", (ev) => ev.preventDefault());
  EL_ev.addEventListener("drop", ondrop);
};

const onstart = (ev) => EL_drag = ev.currentTarget;

const ondrop = (ev) => {
  if (!EL_drag) return;

  ev.preventDefault();
  
  const EL_targ = ev.currentTarget;
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