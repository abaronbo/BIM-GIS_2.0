import * as THREE from "three";
import * as WEBIFC from "web-ifc";
import * as BUI from "@thatopen/ui";
import Stats from "stats.js";
import * as OBC from "@thatopen/components";
import * as OBCF from "@thatopen/components-front";
import * as CUI from '@thatopen/ui-obc';
import { Highlighter } from "@thatopen/components-front";


BUI.Manager.init();

// Function to parse query parameters
function getQueryParams(param: string): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get(param);
}

// Retrieve ifcUrl, refBag, and globalIds
const ifcUrl = getQueryParams("ifcUrl");
const refBag = getQueryParams("ref_bag_id");
const globalIdsParam = getQueryParams("globalIds");

let globalIds: string[] = [];
if (globalIdsParam) {
  try {
    const decodedParam = decodeURIComponent(globalIdsParam);
    globalIds = JSON.parse(decodedParam);
    console.log("Retrieved globalIds from URL:", globalIds);
  } catch (error) {
    console.error("Error parsing globalIds:", error);
  }
} else {
  console.warn("globalIds parameter not found in URL.");
}

if (ifcUrl) {
  localStorage.setItem("ifcUrl", ifcUrl);
  console.log("IFC URL stored in localStorage:", ifcUrl);
}

if (refBag) {
  localStorage.setItem("refBag", refBag);
  console.log("refBag stored in localStorage:", refBag);
}

if (globalIds.length > 0) {
  localStorage.setItem("globalIds", JSON.stringify(globalIds));
  console.log("globalIds stored in localStorage:", globalIds);
}

// Reference to the viewport and properties panel divs from the HTML
const appDiv = document.getElementById("app") as HTMLElement;
const viewport = document.createElement("bim-viewport");
viewport.style.flex = "1";  
viewport.style.height = "100vh";
viewport.style.width = "100%";

// Create and initialize components
const components = new OBC.Components();
const worlds = components.get(OBC.Worlds);
const world = worlds.create<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBCF.PostproductionRenderer>();

const sceneComponent = new OBC.SimpleScene(components);
sceneComponent.setup();
world.scene = sceneComponent;

const rendererComponent = new OBCF.PostproductionRenderer(components, viewport);
world.renderer = rendererComponent;

const cameraComponent = new OBC.OrthoPerspectiveCamera(components);
world.camera = cameraComponent;
cameraComponent.controls.setLookAt(12, 6, 8, 0, 0, -10);

world.renderer.postproduction.enabled = true;
world.renderer.postproduction.customEffects.outlineEnabled = true;

// Ensure the renderer resizes dynamically when the window is resized
window.addEventListener("resize", () => {
  rendererComponent.resize();
  cameraComponent.updateAspect();
});

// Initialize components
components.init();

const grids = components.get(OBC.Grids);
grids.create(world);

// Setting up the fragment manager and loader
const fragments = components.get(OBC.FragmentsManager);
const fragmentIfcLoader = components.get(OBC.IfcLoader);

// Calibrate the converter
await fragmentIfcLoader.setup();
fragmentIfcLoader.settings.webIfc.COORDINATE_TO_ORIGIN = true;

// Load the IFC file and convert it into fragments
async function loadIfcToFragments() {
  const ifcUrl = getQueryParams('ifcUrl');
  console.log("IFC URL from query parameters:", ifcUrl);
  if (!ifcUrl) {
    console.error('No IFC URL provided');
    return null;
  }

  try {
    const file = await fetch(ifcUrl);
    const data = await file.arrayBuffer();
    const buffer = new Uint8Array(data);
    const model = await fragmentIfcLoader.load(buffer);
    world.scene.three.add(model);

    for (const child of model.children) {
      if (child instanceof THREE.Mesh) {
        world.meshes.add(child);
      }
    }

    fragments.onFragmentsLoaded.add((loadedModel) => {
      console.log('Fragments Loaded', loadedModel);
    });

    return model;
  } catch (error) {
    console.error('Error loading IFC file:', error);
    return null;
  }
}

// Load the IFC model and trigger fragment generation
const model = await loadIfcToFragments();

if (model) {
  // Proceed only if the model is successfully loaded

  // Relation index and properties using the model (not fragments)
  const indexer = components.get(OBC.IfcRelationsIndexer);
  await indexer.process(model);

  // Properties Table
  const [propertiesTable, updatePropertiesTable] = CUI.tables.elementProperties({
    components,
    fragmentIdMap: {},
  });

  propertiesTable.preserveStructureOnFilter = true;
  propertiesTable.indentationInText = false;

  let currentFragmentIdMap = {}; // Declare globally to store the current fragment map

  // Highlighter for selection
  const highlighter = components.get(OBCF.Highlighter);
  highlighter.setup({ world });
  
  // Event to update fragmentIdMap on highlight
  highlighter.events.select.onHighlight.add((fragmentIdMap) => {
    updatePropertiesTable({ fragmentIdMap });
    console.log("Updated fragmentIdMap:", fragmentIdMap);
    currentFragmentIdMap = fragmentIdMap; // Store the latest fragmentIdMap
  });
  
  // Event to clear fragmentIdMap on deselect
  highlighter.events.select.onClear.add(() => {
    updatePropertiesTable({ fragmentIdMap: {} });
    currentFragmentIdMap = {}; // Clear the global variable
    console.log("Cleared fragmentIdMap");
  });

// Panel for properties UI
const propertiesPanel = BUI.Component.create(() => {
  const onTextInput = (e: Event) => {
    const input = e.target as BUI.TextInput;
    propertiesTable.queryString = input.value !== "" ? input.value : null;
    
    // Log the search query to the console
    console.log("Properties Table Search Query:", propertiesTable.queryString);
  };

  const expandTable = (e: Event) => {
    const button = e.target as BUI.Button;
    propertiesTable.expanded = !propertiesTable.expanded;
    button.label = propertiesTable.expanded ? "Collapse" : "Expand";
    
    // Log the expanded state of the table to the console
    console.log("Properties Table Expanded:", propertiesTable.expanded);
  };

  return BUI.html`
    <bim-panel label="Properties">
      <bim-panel-section label="Element Data">
        <div style="display: flex; gap: 0.5rem;">
          <bim-button @click=${expandTable} label=${propertiesTable.expanded ? "Collapse" : "Expand"}></bim-button> 
        </div> 
        <bim-text-input @input=${onTextInput} placeholder="Search Property" debounce="250"></bim-text-input>
        ${propertiesTable}
      </bim-panel-section>
    </bim-panel>
  `;
});

const logGlobalIdAndSendToServer = async (
  selectedType: string,
  selectedCategory: string,
  fdmHeight: string,
  fdmWidth: string,
  yearOfReview: string
) => {
  const tsvData = propertiesTable.tsv.split('\n');
  console.log("TSV Data:", propertiesTable.tsv);
  

  const globalIdLine = tsvData.find(line => line.startsWith("GlobalId"));
  const nameLine = tsvData.find(line => line.startsWith("Name") && !line.includes("Value"));
  const classLine = tsvData.find(line => line.startsWith("Class"));

  const globalId = globalIdLine ? globalIdLine.split('\t')[1] : null;
  const name = nameLine ? nameLine.split('\t')[1] : null;
  const classType = classLine ? classLine.split('\t')[1] : null;
  const refBag = localStorage.getItem("refBag");
  console.log("Payload being sent to backend:", {
    refBag,
    globalId,
    name,
    classType,
    fragmentIdMap: currentFragmentIdMap,
    type: selectedType,
    category: selectedCategory,
    height: fdmHeight,
    width: fdmWidth,
    yearOfReview,
  });

  // Esure all required fields are present
  if (globalId && refBag) {
    try {
      const csrfToken = getCsrfToken();

      // Construct the headers object with TypeScript compliance
      const headers: HeadersInit = {
        "Content-Type": "application/json",
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      };

      // Include all the data in the POST body
      const response = await fetch("http://127.0.0.1:8000/ifcupload/save-flood-defense/", {
        method: "POST",
        headers,
        body: JSON.stringify({
          refBag,
          globalId,
          name,
          classType,
          fragmentIdMap: currentFragmentIdMap,
          type: selectedType, 
          category: selectedCategory, 
          height: fdmHeight, 
          width: fdmWidth, 
          yearOfReview, 
        }),
      });

      if (response.ok) {
        console.log("Flood defense mechanism saved successfully.");
      } else {
        const errorData = await response.json();
        console.error("Failed to save flood defense mechanism:", errorData);
      }
    } catch (error) {
      console.error("Error:", error);
    }
  } else {
    console.error("Missing globalId or refBag.");
  }
};




// Helper function to retrieve the CSRF token from a meta tag
function getCsrfToken(): string | undefined {
  const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  if (!token) {
    console.warn("CSRF token not found in meta tags.");
  }
  return token || undefined; // Return undefined if token is null
}


const fdmPanel = BUI.Component.create<BUI.PanelSection>(() => {
  let selectedType = "Flexible water barrier"; // Default value
  let selectedCategory = "Regional flood defense"; // Default value
  let fdmHeight = "";
  let fdmWidth = "";
  let yearOfReview = "";

  return BUI.html`
    <bim-panel label="Flood Defense Mechanism" class="options-menu">
      <bim-panel-section label="Define FDM">
        <!-- Dropdown for Type -->
        <bim-label>Type</bim-label>
        <select
          @change="${(e: Event) => {
            selectedType = (e.target as HTMLSelectElement).value;
            console.log("Selected Type:", selectedType);
          }}">
          <option value="Flexible water barrier">Flexible water barrier</option>
          <option value="Wall construction">Wall construction</option>
          <option value="Cofferdam">Cofferdam</option>
          <option value="Civil work">Civil work</option>
          <option value="High grounds">High grounds</option>
          <option value="Dune">Dune</option>
          <option value="Dike">Dike</option>
          <option value="Dam">Dam</option>
        </select>

        <!-- Dropdown for Category -->
        <bim-label>Category</bim-label>
        <select
          @change="${(e: Event) => {
            selectedCategory = (e.target as HTMLSelectElement).value;
            console.log("Selected Category:", selectedCategory);
          }}">
          <option value="Regional flood defense">Regional flood defense</option>
          <option value="Primary flood defense">Primary flood defense</option>
          <option value="Other flood defense">Other flood defense</option>
          <option value="Foreland barrier">Foreland barrier</option>
          <option value="Compartmentalization barrier">Compartmentalization barrier</option>
          <option value="Barrier alone regional rivers and canals">Barrier alone regional rivers and canals</option>
          <option value="Polder dike">Polder dike</option>
        </select>

        <!-- Input for Height -->
        <bim-label>Height (cm)</bim-label>
        <input type="number" @input="${(e: Event) => {
          fdmHeight = (e.target as HTMLInputElement).value;
          console.log("FDM Height:", fdmHeight);
        }}"/>

        <!-- Input for Width -->
        <bim-label>Width (cm)</bim-label>
        <input type="number" @input="${(e: Event) => {
          fdmWidth = (e.target as HTMLInputElement).value;
          console.log("FDM Width:", fdmWidth);
        }}"/>

        <!-- Input for Year of Review -->
        <bim-label>Year of Review</bim-label>
        <input type="number" @input="${(e: Event) => {
          yearOfReview = (e.target as HTMLInputElement).value;
          console.log("Year of Review:", yearOfReview);
        }}"/>

        <!-- Save Button -->
        <bim-button
          label="Save FDM"
          @click="${() => {
            logGlobalIdAndSendToServer(selectedType, selectedCategory, fdmHeight, fdmWidth, yearOfReview);
          }}"
        />
      </bim-panel-section>
    </bim-panel>
  `;
});


  // // Tree Panel for Model Relations (using the model directly)
  // const [relationsTree, updateRelationsTree] = CUI.tables.relationsTree({
  //   components,
  //   models: [model],  // Pass the IFC model to the relations tree
  // });

  // relationsTree.preserveStructureOnFilter = true;

  // const treePanel = BUI.Component.create(() => {
  //   const onSearch = (e: Event) => {
  //     const input = e.target as BUI.TextInput;
  //     relationsTree.queryString = input.value;
  //   };

  //   return BUI.html`
  //     <bim-panel label="Relations Tree">
  //       <bim-panel-section label="Model Tree">
  //         <bim-text-input @input=${onSearch} placeholder="Search..." debounce="200"></bim-text-input>
  //         ${relationsTree}
  //       </bim-panel-section>
  //     </bim-panel>
  //   `;
  // });

  // Create a container div to hold the left panel and the viewport
  const container = document.createElement('div');
  container.style.display = "flex";
  container.style.height = "100vh";

  // Left Panel for Tree and Properties
  const leftPanel = document.createElement('div');
  leftPanel.style.width = "30rem";
  leftPanel.style.display = "flex";
  leftPanel.style.flexDirection = "column";
  leftPanel.style.overflowY = "auto"; // Add scroll if content overflows

  // Append treePanel and propertiesPanel to leftPanel
  // leftPanel.appendChild(treePanel);
  leftPanel.appendChild(propertiesPanel);

  // Append the defense mechanism button to the left panel
  leftPanel.appendChild(fdmPanel);

  // Append leftPanel and viewport to the container
  container.appendChild(leftPanel);
  container.appendChild(viewport);

  // Append the container to the main app div
  appDiv.appendChild(container);

  // Getting the plans using the model (not fragments)
  const plans = components.get(OBCF.Plans);
  plans.world = world;
  await plans.generate(model);

  // Verify that plans are generated
  console.log('Plans Generated:', plans.list);

  // Prepare variables for use in the plansPanel component
  const minGloss = world.renderer!.postproduction.customEffects.minGloss;
  const whiteColor = new THREE.Color("white");
  const defaultBackground = world.scene.three.background;

  // Final adjustments for culling and floor plans
  const cullers = components.get(OBC.Cullers);
  const culler = cullers.create(world);
  for (const fragment of fragments.list.values()) {
    culler.add(fragment.mesh);
  }
  culler.needsUpdate = true;

  world.camera.controls.addEventListener("sleep", () => {
    culler.needsUpdate = true;
  });

  const classifier = components.get(OBC.Classifier);
  const edges = components.get(OBCF.ClipEdges);

  classifier.byModel(model.uuid, model);
  classifier.byEntity(model);

  const modelItems = classifier.find({ models: [model.uuid] });

  const thickItems = classifier.find({
    entities: ["IFCWALLSTANDARDCASE", "IFCWALL"],
  });

  const thinItems = classifier.find({
    entities: ["IFCDOOR", "IFCWINDOW", "IFCPLATE", "IFCMEMBER"],
  });

  const grayFill = new THREE.MeshBasicMaterial({ color: "gray", side: 2 });
  const blackLine = new THREE.LineBasicMaterial({ color: "black" });
  const blackOutline = new THREE.MeshBasicMaterial({
    color: "black",
    opacity: 0.5,
    side: 2,
    transparent: true,
  });

  edges.styles.create(
    "thick",
    new Set(),
    world,
    blackLine,
    grayFill,
    blackOutline,
  );

  for (const fragID in thickItems) {
    const foundFrag = fragments.list.get(fragID);
    if (!foundFrag) continue;
    const { mesh } = foundFrag;
    edges.styles.list.thick.fragments[fragID] = new Set(thickItems[fragID]);
    edges.styles.list.thick.meshes.add(mesh);
  }

  edges.styles.create("thin", new Set(), world);

  for (const fragID in thinItems) {
    const foundFrag = fragments.list.get(fragID);
    if (!foundFrag) continue;
    const { mesh } = foundFrag;
    edges.styles.list.thin.fragments[fragID] = new Set(thinItems[fragID]);
    edges.styles.list.thin.meshes.add(mesh);
  }

  await edges.update(true);

  // Now, plansPanel 
  const plansPanel = BUI.Component.create(() => {
    // Create buttons for each floor plan
    const planButtons = plans.list.map(plan => BUI.html`
      <bim-button label="${plan.name}"
        @click="${() => {
          world.renderer!.postproduction.customEffects.minGloss = 0.1;
          highlighter.backupColor = whiteColor;
          classifier.setColor(modelItems, whiteColor);
          world.scene.three.background = whiteColor;
          plans.goTo(plan.id);
          culler.needsUpdate = true;
        }}">
      </bim-button>
    `);

    // Add an "Exit" button to exit the floor plan mode
    const exitButton = BUI.html`
      <bim-button label="Exit"
        @click="${() => {
          highlighter.backupColor = null;
          highlighter.clear();
          world.renderer!.postproduction.customEffects.minGloss = minGloss;
          classifier.resetColor(modelItems);
          world.scene.three.background = defaultBackground;
          plans.exitPlanView();
          culler.needsUpdate = true;
        }}">
      </bim-button>
    `;

    return BUI.html`
      <bim-panel active label="Floor Plans" class="options-menu">
        <bim-panel-section name="floorPlans" label="Plan list">
          ${planButtons}
          ${exitButton}
        </bim-panel-section>
      </bim-panel>
    `;
  });

  // Append the plansPanel to the leftPanel
  leftPanel.appendChild(plansPanel);

  // // Edge measurements
  // const dimensions = components.get(OBCF.EdgeMeasurement);
  // dimensions.world = world;
  // dimensions.enabled = false;  // Set to false on startup

  // let saved: number[][];

  // // Use double-click to create edge measurements
  // container.ondblclick = () => {
  //   if (dimensions.enabled) {
  //     dimensions.create();
  //   }
  // };

  // // Handle other keyboard events for edge measurements
  // window.addEventListener("keydown", (event) => {
  //   if (event.code === "KeyO") {
  //     dimensions.delete();
  //   } else if (event.code === "KeyS") {
  //     saved = dimensions.get();
  //     dimensions.deleteAll();
  //   } else if (event.code === "KeyL") {
  //     if (saved) {
  //       dimensions.set(saved);
  //     }
  //   }
  // });

  // // Length measurements
  // const ldimensions = components.get(OBCF.LengthMeasurement);
  // ldimensions.world = world;
  // ldimensions.enabled = false;  // Set to false on startup
  // ldimensions.snapDistance = 1;

  // // Use double-click to create length measurements
  // container.ondblclick = () => {
  //   if (ldimensions.enabled) {
  //     ldimensions.create();
  //   }
  // };

  // // Handle delete key for length measurements
  // window.onkeydown = (event) => {
  //   if (event.code === "Delete" || event.code === "Backspace") {
  //     ldimensions.delete();
  //   }
  // };

  // const areadimensions = components.get(OBCF.FaceMeasurement);
  // areadimensions.world = world;
  // areadimensions.enabled =false;

  // let areasaved: OBCF.SerializedAreaMeasure[];

  // // Use "A" key to create face measurements instead of double-click
  // window.addEventListener("keydown", (event) => {
  //   if (event.code === "KeyA") {
  //     areadimensions.create();
  //   } else if (event.code === "KeyO") {
  //     areadimensions.delete();
  //   } else if (event.code === "KeyS") {
  //     saved = dimensions.get();
  //     areadimensions.deleteAll();
  //   } else if (event.code === "KeyL") {
  //     if (saved) {
  //       areadimensions.set(areasaved);
  //     }
  //   }
  // });

  // // Clipper functionality
  // const clipper = components.get(OBC.Clipper);
  // clipper.enabled = false;  // Disable by default

  // // Delete any existing clipping planes when the file is opened or reloaded
  // clipper.deleteAll();

  // // Use "C" key to create clipping planes
  // window.addEventListener("keydown", (event) => {
  //   if (event.code === "KeyC") {
  //     if (clipper.enabled) {
  //       clipper.create(world);
  //     }
  //   } else if (event.code === "Delete" || event.code === "Backspace") {
  //     if (clipper.enabled) {
  //       clipper.delete(world);
  //     }
  //   }
  // });

  // // UI panel to control the clipper, measurements, and other elements
  // const panel = BUI.Component.create<BUI.PanelSection>(() => {
  //   return BUI.html`
  //     <bim-panel active label="Length Measurement Tutorial" class="options-menu">
  //       <bim-panel-section collapsed label="Controls">
  //           <bim-label>Create measurement: Double click</bim-label>  
  //           <bim-label>Delete measurement: Delete</bim-label>  
  //       </bim-panel-section>
        
  //       <bim-panel-section collapsed label="Others">
  //         <bim-checkbox label="Measurements enabled" 
  //           @change="${({ target }: { target: BUI.Checkbox }) => {
  //             ldimensions.enabled = target.value;
  //           }}">  
  //         </bim-checkbox>       
  //         <bim-checkbox label="Measurements visible" 
  //           @change="${({ target }: { target: BUI.Checkbox }) => {
  //             ldimensions.visible = target.value;
  //           }}">  
  //         </bim-checkbox> 
  //         <bim-checkbox label="Preview edge measurements" 
  //           @change="${({ target }: { target: BUI.Checkbox }) => {
  //             dimensions.enabled = target.value;
  //           }}">  
  //         </bim-checkbox> 

  //         <bim-checkbox label="Preview area measurements" 
  //         @change="${({ target }: { target: BUI.Checkbox }) => {
  //           areadimensions.enabled = target.value;
  //         }}">  
  //       </bim-checkbox> 
          
  //         <bim-button label="Delete all"
  //           @click="${() => {
  //             ldimensions.deleteAll();
  //             areadimensions.deleteAll();
  //           }}">
  //         </bim-button>
  //       </bim-panel-section>
  //     </bim-panel>
  //   `;
  // });

  // // Append the panel to the left panel
  // leftPanel.appendChild(panel);

//   // Clipper control panel
//   const clipanel = BUI.Component.create<BUI.PanelSection>(() => {
//     return BUI.html`
//       <bim-panel label="Clipper Tutorial" class="options-menu">
//         <bim-panel-section collapsed label="Commands">
//           <bim-label>Press "C": Create clipping plane</bim-label>
//           <bim-label>Delete key: Delete clipping plane</bim-label>
//         </bim-panel-section>
        
//         <bim-panel-section collapsed label="Others">
//           <bim-checkbox label="Clipper enabled" 
//             @change="${({ target }: { target: BUI.Checkbox }) => {
//               clipper.enabled = target.value;
//             }}">
//           </bim-checkbox>

//           <bim-checkbox label="Clipper visible" checked 
//             @change="${({ target }: { target: BUI.Checkbox }) => {
//               clipper.visible = target.value;
//             }}">
//           </bim-checkbox>
          
//           <bim-color-input 
//             label="Planes Color" color="#202932" 
//             @input="${({ target }: { target: BUI.ColorInput }) => {
//               clipper.material.color.set(target.color);
//             }}">
//           </bim-color-input>
          
//           <bim-number-input 
//             slider step="0.01" label="Planes opacity" value="0.2" min="0.1" max="1"
//             @change="${({ target }: { target: BUI.NumberInput }) => {
//               clipper.material.opacity = target.value;
//             }}">
//           </bim-number-input>
          
//           <bim-number-input 
//             slider step="0.1" label="Planes size" value="5" min="2" max="10"
//             @change="${({ target }: { target: BUI.NumberInput }) => {
//               clipper.size = target.value;
//             }}">
//           </bim-number-input>
          
//           <bim-button 
//             label="Delete all" 
//             @click="${() => {
//               clipper.deleteAll();
//             }}">  
//           </bim-button>        
//         </bim-panel-section>
//       </bim-panel>
//     `;
//   });

//   // Append the clipper control panel to the left panel
//   leftPanel.appendChild(clipanel);
// } else {
//   console.error("Model failed to load.");
// }

const globalIdsString = localStorage.getItem("globalIds");
if (globalIdsString) {
  try {
    globalIds = JSON.parse(globalIdsString);
    console.log("Retrieved globalIds from localStorage:", globalIds);
  } catch (error) {
    console.error("Error parsing globalIds:", error);
  }
} else {
  console.warn("No globalIds found in localStorage.");
}

const fragmentMap = fragments.guidToFragmentIdMap(globalIds);
console.log("Constructed FragmentIdMap:", fragmentMap);

const highlighter2 = components.get(OBCF.Highlighter);

  // Step 4: Highlight using `highlightByID`
  try {
    const selectionName = "New_Selectionno?";
    const selectionColor = new THREE.Color(0xff0000); // Red color

    // Add the new selection with the specified color
    highlighter2.add(selectionName, selectionColor);

    // Highlight the fragments
    await highlighter2.highlightByID(selectionName, fragmentMap, true, false);
    console.log(`Highlighted fragments for selection ${selectionName}`, fragmentMap);
  } catch (error) {
    console.error("Error during highlighting:", error);
  }
}
