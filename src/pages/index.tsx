import { FormEvent, useState } from 'react';
import Image from 'next/image';
import { v4 as uuid } from 'uuid';
import { FileUploader } from "react-drag-drop-files";
import { FiPlus } from "react-icons/fi";

import useAppStore from '../useAppStore';
import { IConversation } from '@/utils/interfaces';
import Humana_Logo from "../assets/humana-logo.png";

const fileTypes = ['PDF'];

function App() {
  const uploadedFiles = useAppStore(state => state.uploadedFiles);
  const setUploadedFiles = useAppStore(state => state.setUploadedFiles);

  const selectedFile = useAppStore(state => state.selectedFile);
  const setSelectedFile = useAppStore(state => state.setSelectedFile);

  const [conversations, setConversations] = useState<IConversation[]>([])

  const [input, setInput] = useState('');

  const handleQuestionAsked = async (evt: FormEvent<HTMLFormElement>) => {
    evt.preventDefault();
    if (!selectedFile) return;
    const question: IConversation = { text: input, type: 'question' };
    
    setConversations(conversations => [...conversations, question]);
    
    await getResponse(selectedFile?.file, question.text);
  }
  
  const getResponse = async (file: File, question: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('prompt', question);
    
    try {
      const response = await fetch('http://127.0.0.1:5328/api/process_prompt', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      const answer: IConversation = { text: result.answer, type: 'answer' };
      
      setConversations(conversations => [...conversations, answer]);
    } catch (error) {
      console.error('Error processing file:', error);
    }
  }

  const handleFileUpload = async (file: File) => {
    const fileUrl = URL.createObjectURL(file);

    const newFile = {
      id: uuid(),
      url: fileUrl,
      file
    };

    setUploadedFiles([...uploadedFiles, newFile]);
    setSelectedFile(newFile);
  };

  return (
    <div className='w-full h-screen flex flex-col justify-between'>
      <div className="navbar px-12 py-4 text-black">
        <div className="navbar-start">
          <a href="/">
            <Image src={Humana_Logo} alt='Humana H Logo' width={200} />
          </a>
        </div>

        <div className="navbar-end w-full flex justify-end">
          <ul className="gap-x-8 hidden lg:flex">
            <li><a href="https://www.humana.com/" target="_blank">EOC Documentation</a></li>
            <li><a href="https://www.humana.com/" target="_blank">Strider</a></li>
            <li><a href="https://www.humana.com/" target="_blank">More</a></li>
          </ul>

          <div className="dropdown dropdown-end lg:hidden">
            <label tabIndex={0} className="btn btn-ghost btn-circle">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h7" /></svg>
            </label>
            <ul tabIndex={0} className="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-white rounded-box w-52">
              <li><a href="https://www.humana.com/" target="_blank">EOC Documentation</a></li>
              <li><a href="https://www.humana.com/" target="_blank">Strider</a></li>
              <li><a href="https://www.humana.com/" target="_blank">More</a></li>
            </ul>
          </div>
        </div>
      </div>

      <div className="flex w-full max-h-full h-full overflow-y-hidden">
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
              <button className={`btn rounded-xl md:w-full bg-[#78BE20] text-white border-none shadow-md hover:bg-gray-100 ${selectedFile?.id !== elm.id ? 'bg-opacity-25' : ''}`}>
                <p className='truncate'>{elm.file.name}</p>
              </button>
            </div>
          ))}
        </div>

        <div className="w-2/6 bg-white">
          {selectedFile && <object data={selectedFile.url} type="application/pdf" width="100%" height="100%">
            <p>Alternative text - include a link <a href="https://www.clickdimensions.com/links/TestPDFfile.pdf">to the PDF!</a></p>
          </object>}
        </div>

        <div className="w-3/6 bg-gray-100 p-2 flex flex-col">
          <div className="flex-grow overflow-y-auto">
            {conversations.map((elm, index) => (
              elm.type === 'question' ? (<div key={index} className={`chat chat-end`}>
                <div className="chat-bubble w-full bg-[#78BE20] bg-opacity-25 text-black">
                  <p>{elm.text}</p>
                </div>
              </div>) : (<div key={index} className={`chat chat-start`}>
                <div className="chat-bubble w-full bg-gray-200 text-black">
                  <p>{elm.text}</p>
                </div>
              </div>)
            ))}
          </div>
          <form onSubmit={handleQuestionAsked} className="h-16 mt-2 flex justify-center input-group">
            <input placeholder="Ask me a question" value={input} onChange={(evt) => setInput(evt.target.value)} className="input max-w-3xl w-full mx-auto h-full bg-gray-200 focus:outline-none rounded-full focus:border-none" />

          </form>
        </div>
      </div>

      <div className="bg-[#78BE20] text-white text-xs sm:text-sm sm:py-2">
        <div className="w-3/4 mx-auto flex flex-wrap justify-center items-center">
          <a href="https://www.humana.com/" target="_blank" className="m-2">© 2024 Humana</a>
        </div>
      </div>
    </div>
  )
}

export default App;