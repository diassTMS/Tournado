const draggables = document.querySelectorAll(".task");
const droppables = document.querySelectorAll(".swim-lane");
var task_id= '0';
var emp_id = '0';


draggables.forEach((task) => {
  task.addEventListener("dragstart", () => {
    task.classList.add("is-dragging");
  });
  task.addEventListener("dragend", () => {
    task.classList.remove("is-dragging");
    
    get_assign(task_id, emp_id);

  });
});

droppables.forEach((zone) => {
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();

    const bottomTask = insertAboveTask(zone, e.clientY);
    const curTask = document.querySelector(".is-dragging");

    if (!bottomTask) {
      zone.appendChild(curTask);
    } else {
      zone.insertBefore(curTask, bottomTask);
    }
    task_id = curTask.id;
    emp_id = zone.id;
    });
});

const insertAboveTask = (zone, mouseY) => {
  const els = zone.querySelectorAll(".task:not(.is-dragging)");
  
  let closestTask = null;
  let closestOffset = Number.NEGATIVE_INFINITY;


  els.forEach((task) => {
    const { top } = task.getBoundingClientRect();

    const offset = mouseY - top;

    if (offset < 0 && offset > closestOffset) {
      closestOffset = offset;
      closestTask = task;
    }
  });

  return closestTask;
};

function get_assign(task_id, emp_id){
    $.ajax({
        type: 'GET',
        url: `/entry-assign/${emp_id}/${task_id}/`,
        failure: function(data){
          console.log('failure');
          console.log(data);
        },
      });
}

