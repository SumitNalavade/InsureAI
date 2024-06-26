import { v4 as uuid } from 'uuid';;
import { FileUploader } from "react-drag-drop-files";
import { FiPlus } from "react-icons/fi";

import useAppStore from './useAppStore';
import Humana_Logo from "./assets/humana-logo.png";

const fileTypes = ['PDF'];

function App() {
  const uploadedFiles = useAppStore(state => state.uploadedFiles);
  const setUploadedFiles = useAppStore(state => state.setUploadedFiles);

  const selectedFile = useAppStore(state => state.selectedFile);
  const setSelectedFile = useAppStore(state => state.setSelectedFile);

  const handleFileUpload = (file: File) => {
    const fileUrl = URL.createObjectURL(file);

    const newFile = {
      id: uuid(),
      url: fileUrl,
      file
    }

    setUploadedFiles([...uploadedFiles, newFile]);
    setSelectedFile(newFile);
  };

  console.log(uploadedFiles.reverse());

  return (
    <div className='w-full h-screen flex flex-col justify-between'>
      <div className="navbar px-12 py-6 text-black">
        <div className="navbar-start">
          <a href="/">
            <img src={Humana_Logo} alt="Texas A&M University Logo" className="btn btn-ghost normal-case object-contain transform scale-150 hover:bg-transparent hover:text-current" />
          </a>
        </div>

        <div className="navbar-end w-full flex justify-end">
          <ul className="gap-x-8 hidden lg:flex">
            <li><a href="http://www.oliviahealth.org" target="_blank">EOC Documentation</a></li>
            <li><a href="http://www.oliviahealth.org" target="_blank">Strider</a></li>
            <li><a href="http://www.oliviahealth.org" target="_blank">More</a></li>
          </ul>

          <div className="dropdown dropdown-end lg:hidden">
            <label tabIndex={0} className="btn btn-ghost btn-circle">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h7" /></svg>
            </label>
            <ul tabIndex={0} className="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-white rounded-box w-52">

              <li><a href="http://www.oliviahealth.org" target="_blank">EOC Documentation</a></li>
              <li><a href="http://www.oliviahealth.org" target="_blank">Strider</a></li>
              <li><a href="http://www.oliviahealth.org" target="_blank">More</a></li>
            </ul>
          </div>
        </div>
      </div>

      <div className="flex w-full h-screen">
        <div className="w-1/6 bg-gray-100 p-2 space-y-4">
          <div className="flex gap-2 justify-between items-center">

            <div className='w-full h-full'>
              <FileUploader
                handleChange={handleFileUpload}
                name="file"
                types={fileTypes}
                className={'w-full h-full border-none outline-none'}
              >
                <button
                  className="btn rounded-xl md:w-full bg-white border-none text-black shadow-md hover:bg-gray-100 w-full h-full"
                >
                  <FiPlus />
                  <p>New Chat</p>
                </button>
              </FileUploader>
            </div>


          </div>

          {uploadedFiles.toReversed().map((elm, index) => (
            <div key={index} className="flex gap-2 justify-between items-center" onClick={() => setSelectedFile(elm)}>
              <button className="btn rounded-xl md:w-full bg-[#78BE20] text-white border-none shadow-md hover:bg-gray-100">
                <p className='truncate'>{elm.file.name}</p>
              </button>
            </div>
          ))}
        </div>
        <div className="w-2/5 bg-white">
          {selectedFile && <object data={selectedFile.url} type="application/pdf" width="100%" height="100%">
            <p>Alternative text - include a link <a href="https://www.clickdimensions.com/links/TestPDFfile.pdf">to the PDF!</a></p>
          </object>}
        </div>
        <div className="w-3/5 bg-gray-100">
          <p>3</p>
        </div>
      </div>

      <div className="bg-[#78BE20] text-white text-xs sm:text-sm sm:py-2">
        <div className="w-3/4 mx-auto flex flex-wrap justify-center items-center">
          <a href="https://oliviahealth.org/" target="_blank" className="m-2">© 2024 OliviaHealth</a>
        </div>
      </div>
    </div>
  )
}

export default App
