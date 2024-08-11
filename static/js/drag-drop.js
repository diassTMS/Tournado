let elementsArray = document.querySelectorAll(".float-child");

elementsArray.forEach(function(elem) {
  console.log(elem);
  elem.setAttribute("draggable", "true");
  elem.addEventListener("touchstart", onstart);
  elem.addEventListener("touchmove", (ev) => ev.preventDefault());
  elem.addEventListener("touchend", ondrop);
});

let EL_drag; // Used to remember the dragged element

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
  
  EL_targ.replaceWith(EL_dragClone);
  EL_drag.replaceWith(EL_targClone);
  
  addEvents(EL_targClone); // Reassign events to cloned element
  addEvents(EL_dragClone); // Reassign events to cloned element
  
  EL_drag = undefined;
};

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